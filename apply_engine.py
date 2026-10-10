import asyncio
import logging
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
        self.profile = profile_manager or ProfileManager()
        self.cl_generator = CoverLetterGenerator(self.profile)

        # Order handlers by specificity
        self.handlers = [
            GreenhouseATSHandler(self.profile),
            LeverATSHandler(self.profile),
            GenericATSHandler(self.profile),
        ]

    async def apply(
        self,
        job_url: str,
        job_title: str = "",
        company_name: str = "",
        job_description: str = "",
        headless: bool = False,
        dry_run: bool = True,
        auto_submit: bool = False,
        wait_for_user_seconds: int = 15,
    ) -> Dict[str, Any]:
        logger.info(f"Starting application run for {job_title} at {company_name} ({job_url})")

        cover_letter = self.cl_generator.generate(job_title, company_name, job_description)

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

                # Pick matching handler
                active_handler = None
                for handler in self.handlers:
                    if handler.can_handle(job_url, content):
                        active_handler = handler
                        break

                if not active_handler:
                    active_handler = GenericATSHandler(self.profile)

                logger.info(f"Using handler: {active_handler.__class__.__name__}")

                # Fill form
                result = await active_handler.fill_form(page, cover_letter=cover_letter)

                if auto_submit and not dry_run:
                    logger.info("Auto-submit enabled. Submitting application form...")
                    submitted = await active_handler.submit_form(page)
                    result["submitted"] = submitted
                    await page.wait_for_timeout(3000)
                else:
                    logger.info("Dry-run or interactive mode. Skipping auto-submit.")
                    result["submitted"] = False
                    if not headless:
                        logger.info(f"Leaving browser open for {wait_for_user_seconds} seconds for user review...")
                        await page.wait_for_timeout(wait_for_user_seconds * 1000)

                await browser.close()
                result["status"] = "Applied" if result.get("submitted") else "Processed (Review Required)"
                return result

            except Exception as e:
                logger.exception(f"Error during application execution: {e}")
                await browser.close()
                return {
                    "success": False,
                    "status": "Failed",
                    "error": str(e),
                    "notes": f"Application engine failed: {e}",
                }

def run_apply(job_url: str, job_title: str = "", company_name: str = "", headless: bool = False, dry_run: bool = True, auto_submit: bool = False):
    engine = ApplyEngine()
    return asyncio.run(engine.apply(
        job_url=job_url,
        job_title=job_title,
        company_name=company_name,
        headless=headless,
        dry_run=dry_run,
        auto_submit=auto_submit,
    ))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing ApplyEngine module import...")
