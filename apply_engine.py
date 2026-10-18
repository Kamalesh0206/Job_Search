import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

from profile_manager import ProfileManager
from cover_letter_generator import CoverLetterGenerator
from ats_handlers import (
    GreenhouseATSHandler,
    LeverATSHandler,
    GenericATSHandler,
)

logger = logging.getLogger(__name__)

class ApplyEngine:
    def __init__(self, profile_manager: Optional[ProfileManager] = None):
        self.default_pm = profile_manager or ProfileManager()
        self.cl_generator = CoverLetterGenerator(self.default_pm)

    async def apply(
        self,
        job_url: str,
        job_title: str = "",
        company_name: str = "",
        job_description: str = "",
        profile_id: str = "AI_ENGINEER",
        headless: bool = False,
        dry_run: bool = True,
        auto_submit: bool = False,
        wait_for_user_seconds: int = 15,
    ) -> Dict[str, Any]:
        logger.info(f"Starting application run for {job_title} at {company_name} ({job_url}) [Profile: {profile_id}]")

        # Use profile-specific profile manager and handlers
        pm = ProfileManager(profile_id=profile_id)
        cl_generator = CoverLetterGenerator(pm)

        handlers = [
            GreenhouseATSHandler(pm),
            LeverATSHandler(pm),
            GenericATSHandler(pm),
        ]

        cl_result = cl_generator.generate(
            job_title=job_title,
            company_name=company_name,
            job_description=job_description,
            profile_id=profile_id,
            save_to_disk=True
        )
        cover_letter_text = cl_result.get("cover_letter", "") if isinstance(cl_result, dict) else str(cl_result)
        cover_letter_path = cl_result.get("file_path", "")
        resume_p = pm.get_resume_absolute_path()

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )

            context = await browser.new_context(viewport={"width": 1280, "height": 900})
            page = await context.new_page()

            try:
                logger.info(f"Navigating to {job_url}...")
                await page.goto(job_url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)

                content = await page.content()
                content_lower = content.lower()

                # Check for CAPTCHA or security challenge
                has_captcha = any(c in content_lower for c in [
                    "g-recaptcha", "hcaptcha", "cf-turnstile", "captcha",
                    "security check to access", "verify you are human", "please verify you are a human"
                ])

                if has_captcha:
                    logger.warning("CAPTCHA or bot protection challenge detected. Manual completion required.")
                    await browser.close()
                    return {
                        "success": False,
                        "status": "MANUAL_ACTION_REQUIRED",
                        "submitted": False,
                        "notes": "CAPTCHA challenge detected on application page. Manual completion required.",
                        "error_details": "CAPTCHA challenge detected",
                        "resume_used": resume_p.name if resume_p else "",
                        "cover_letter_path": cover_letter_path,
                        "submission_timestamp": datetime.now().isoformat()
                    }

                # Pick matching handler
                active_handler = None
                for handler in handlers:
                    if handler.can_handle(job_url, content):
                        active_handler = handler
                        break

                if not active_handler:
                    active_handler = GenericATSHandler(pm)

                logger.info(f"Using handler: {active_handler.__class__.__name__}")

                # Fill form
                result = await active_handler.fill_form(page, cover_letter=cover_letter_text)

                if auto_submit and not dry_run:
                    logger.info("Submitting application form...")
                    try:
                        submitted = await active_handler.submit_form(page)
                        result["submitted"] = submitted
                        await page.wait_for_timeout(3000)

                        if submitted:
                            result["status"] = "APPLIED"
                            result["submission_timestamp"] = datetime.now().isoformat()
                            result["submission_response"] = "Application successfully submitted to employer ATS"
                        else:
                            result["status"] = "SUBMISSION_FAILED"
                            result["error_details"] = "Submission button not found or submission was blocked"
                    except Exception as submit_err:
                        logger.error(f"Form submission failed: {submit_err}")
                        result["submitted"] = False
                        result["status"] = "SUBMISSION_FAILED"
                        result["error_details"] = str(submit_err)
                else:
                    logger.info("Dry-run or manual review mode. Skipping auto-submit.")
                    result["submitted"] = False
                    result["status"] = "READY_TO_APPLY"
                    if not headless:
                        logger.info(f"Leaving browser open for {wait_for_user_seconds} seconds for user review...")
                        await page.wait_for_timeout(wait_for_user_seconds * 1000)

                await browser.close()
                result["cover_letter_path"] = cover_letter_path
                result["resume_used"] = resume_p.name if resume_p else ""
                return result

            except Exception as e:
                logger.exception(f"Error during application execution: {e}")
                await browser.close()
                return {
                    "success": False,
                    "status": "SUBMISSION_FAILED",
                    "submitted": False,
                    "error_details": str(e),
                    "notes": f"Application engine error: {e}",
                    "cover_letter_path": cover_letter_path,
                    "resume_used": resume_p.name if resume_p else ""
                }

def run_apply(
    job_url: str,
    job_title: str = "",
    company_name: str = "",
    job_description: str = "",
    profile_id: str = "AI_ENGINEER",
    headless: bool = False,
    dry_run: bool = True,
    auto_submit: bool = False
):
    engine = ApplyEngine()
    return asyncio.run(engine.apply(
        job_url=job_url,
        job_title=job_title,
        company_name=company_name,
        job_description=job_description,
        profile_id=profile_id,
        headless=headless,
        dry_run=dry_run,
        auto_submit=auto_submit,
    ))

def evaluate_auto_apply_eligibility(
    match_score: int,
    mandatory_pass: bool,
    job_is_open: bool = True,
    not_already_applied: bool = True,
    application_data_is_valid: bool = True,
    submission_method_is_authorized: bool = True,
    threshold: int = 70,
    daily_limit_reached: bool = False
) -> Dict[str, Any]:
    """
    Enforces the automatic application business rule:
    IF match_score > 70
    AND mandatory_requirements_pass
    AND job_is_open
    AND not_already_applied
    AND application_data_is_valid
    AND submission_method_is_authorized
    AND not daily_limit_reached
    THEN submit_application

    If score == 70: do not auto-submit -> manual review (READY_TO_APPLY)
    If score <= 70: manual review queue (READY_TO_APPLY if >= 60 else BELOW_THRESHOLD)
    """
    if not job_is_open:
        return {
            "eligible": False,
            "status": "CLOSED",
            "reason": "Job is no longer open"
        }

    if not not_already_applied:
        return {
            "eligible": False,
            "status": "APPLIED",
            "reason": "Already applied to this vacancy; duplicate submission prevented"
        }

    if not mandatory_pass:
        return {
            "eligible": False,
            "status": "MANUAL_ACTION_REQUIRED",
            "reason": "Mandatory qualifications check failed; requires manual review"
        }

    if not application_data_is_valid:
        return {
            "eligible": False,
            "status": "MANUAL_ACTION_REQUIRED",
            "reason": "Required application data is missing or incomplete"
        }

    # Strict inequality (> 70): exactly 70% does not auto-submit
    if match_score <= threshold:
        target_st = "READY_TO_APPLY" if match_score >= 60 else "BELOW_THRESHOLD"
        return {
            "eligible": False,
            "status": target_st,
            "reason": f"Match score {match_score}% is not greater than {threshold}% threshold; placed in manual review queue"
        }

    if not submission_method_is_authorized:
        return {
            "eligible": False,
            "status": "READY_TO_APPLY",
            "reason": "Profile automatic submission is disabled by user settings; placed in manual review queue"
        }

    if daily_limit_reached:
        return {
            "eligible": False,
            "status": "READY_TO_APPLY",
            "reason": "Daily application limit reached for profile; placed in manual review queue"
        }

    return {
        "eligible": True,
        "status": "READY_TO_APPLY",
        "reason": f"Match score {match_score}% > {threshold}% and all eligibility checks passed for automatic submission"
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing ApplyEngine module and eligibility rule...")
    engine = ApplyEngine()
    print("ApplyEngine initialized successfully.")

    # Verification of eligibility rule
    e_75 = evaluate_auto_apply_eligibility(75, True)
    assert e_75["eligible"] is True, "75% should be eligible"

    e_70 = evaluate_auto_apply_eligibility(70, True)
    assert e_70["eligible"] is False, "70% should NOT be eligible"
    assert e_70["status"] == "READY_TO_APPLY"

    e_60 = evaluate_auto_apply_eligibility(60, True)
    assert e_60["eligible"] is False, "60% should NOT be eligible"
    assert e_60["status"] == "READY_TO_APPLY"

    e_disq = evaluate_auto_apply_eligibility(85, False)
    assert e_disq["eligible"] is False, "Disqualified should NOT be eligible"
    assert e_disq["status"] == "MANUAL_ACTION_REQUIRED"

    e_dup = evaluate_auto_apply_eligibility(85, True, not_already_applied=False)
    assert e_dup["eligible"] is False, "Duplicate should NOT be eligible"

    e_disabled = evaluate_auto_apply_eligibility(85, True, submission_method_is_authorized=False)
    assert e_disabled["eligible"] is False, "Disabled auto-apply should NOT be eligible"

    print("[PASS] Automatic application rule checks passed.")

