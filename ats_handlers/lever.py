import logging
from typing import Dict, Any
from .base import BaseATSHandler

logger = logging.getLogger(__name__)

class LeverATSHandler(BaseATSHandler):
    def can_handle(self, url: str, content: str = "") -> bool:
        return "jobs.lever.co" in url.lower() or "lever-form" in content.lower() or "lever.co" in url.lower()

    async def fill_form(self, page, cover_letter: str = "") -> Dict[str, Any]:
        filled_count = 0
        p = self.profile.personal
        links = self.profile.links

        # Full Name
        if await page.locator("input[name='name']").count() > 0:
            await page.fill("input[name='name']", self.profile.get_full_name())
            filled_count += 1

        # Email
        if await page.locator("input[name='email']").count() > 0:
            await page.fill("input[name='email']", p.get("email", ""))
            filled_count += 1

        # Phone
        if await page.locator("input[name='phone']").count() > 0:
            await page.fill("input[name='phone']", p.get("phone", ""))
            filled_count += 1

        # Current Company
        if await page.locator("input[name='org']").count() > 0:
            await page.fill("input[name='org']", "Software Engineering")
            filled_count += 1

        # LinkedIn
        if await page.locator("input[name*='LinkedIn'], input[name='urls[LinkedIn]']").count() > 0:
            await page.fill("input[name*='LinkedIn'], input[name='urls[LinkedIn]']", links.get("linkedin", ""))
            filled_count += 1

        # GitHub
        if await page.locator("input[name*='GitHub'], input[name='urls[GitHub]']").count() > 0:
            await page.fill("input[name*='GitHub'], input[name='urls[GitHub]']", links.get("github", ""))
            filled_count += 1

        # Portfolio / Other Website
        if await page.locator("input[name*='Portfolio'], input[name*='Other'], input[name='urls[Portfolio]']").count() > 0:
            await page.fill("input[name*='Portfolio'], input[name*='Other'], input[name='urls[Portfolio]']", links.get("portfolio") or links.get("website", ""))
            filled_count += 1

        # Resume Upload
        resume_path = self.profile.get_resume_absolute_path()
        if resume_path and resume_path.exists():
            file_input = page.locator("input[type='file'][name='resume'], #resume-upload-input, input[type='file']").first
            if await file_input.count() > 0:
                await file_input.set_input_files(str(resume_path))
                filled_count += 1
                logger.info(f"Attached resume to Lever form: {resume_path}")

        # Comments / Cover Letter
        if cover_letter:
            comments = page.locator("textarea[name='comments'], textarea[name*='cover']").first
            if await comments.count() > 0:
                await comments.fill(cover_letter)
                filled_count += 1

        return {
            "success": True,
            "fields_filled": filled_count,
            "handler": "Lever",
            "notes": f"Filled {filled_count} fields on Lever application form."
        }

    async def submit_form(self, page) -> bool:
        submit_btn = page.locator("button#btn-submit, button[type='submit'], input[type='submit']").first
        if await submit_btn.count() > 0:
            await submit_btn.click()
            return True
        return False
