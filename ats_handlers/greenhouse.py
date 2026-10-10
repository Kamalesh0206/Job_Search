import logging
import re
from typing import Dict, Any
from .base import BaseATSHandler

logger = logging.getLogger(__name__)

class GreenhouseATSHandler(BaseATSHandler):
    def can_handle(self, url: str, content: str = "") -> bool:
        return "greenhouse.io" in url.lower() or "grnhse" in content.lower() or "id=\"application_form\"" in content.lower()

    async def fill_form(self, page, cover_letter: str = "") -> Dict[str, Any]:
        filled_count = 0
        p = self.profile.personal
        links = self.profile.links

        # First Name
        if await page.locator("input#first_name, input[name*='first_name']").count() > 0:
            await page.fill("input#first_name, input[name*='first_name']", p.get("first_name", ""))
            filled_count += 1

        # Last Name
        if await page.locator("input#last_name, input[name*='last_name']").count() > 0:
            await page.fill("input#last_name, input[name*='last_name']", p.get("last_name", ""))
            filled_count += 1

        # Email
        if await page.locator("input#email, input[name*='email']").count() > 0:
            await page.fill("input#email, input[name*='email']", p.get("email", ""))
            filled_count += 1

        # Phone
        if await page.locator("input#phone, input[name*='phone']").count() > 0:
            await page.fill("input#phone, input[name*='phone']", p.get("phone", ""))
            filled_count += 1

        # LinkedIn
        if await page.locator("input[name*='linkedin'], input[id*='linkedin']").count() > 0:
            await page.fill("input[name*='linkedin'], input[id*='linkedin']", links.get("linkedin", ""))
            filled_count += 1

        # Website / Portfolio
        if await page.locator("input[name*='website'], input[name*='portfolio']").count() > 0:
            await page.fill("input[name*='website'], input[name*='portfolio']", links.get("portfolio") or links.get("website", ""))
            filled_count += 1

        # Resume Upload
        resume_path = self.profile.get_resume_absolute_path()
        if resume_path and resume_path.exists():
            file_input = page.locator("input[type='file'][name*='resume'], input[type='file']").first
            if await file_input.count() > 0:
                await file_input.set_input_files(str(resume_path))
                filled_count += 1
                logger.info(f"Attached resume: {resume_path}")

        # Cover Letter Textarea or file
        if cover_letter:
            cl_area = page.locator("textarea[name*='cover_letter'], textarea[id*='cover_letter']").first
            if await cl_area.count() > 0:
                await cl_area.fill(cover_letter)
                filled_count += 1

        # Dynamic questions / select dropdowns heuristics
        selects = page.locator("select")
        count = await selects.count()
        for i in range(count):
            select = selects.nth(i)
            id_or_name = (await select.get_attribute("name") or "") + " " + (await select.get_attribute("id") or "")
            ans = self.profile.get_standard_answer(id_or_name)
            if ans:
                options = await select.locator("option").all_inner_texts()
                for opt in options:
                    if ans.lower() in opt.lower():
                        await select.select_option(label=opt)
                        filled_count += 1
                        break

        return {
            "success": True,
            "fields_filled": filled_count,
            "handler": "Greenhouse",
            "notes": f"Filled {filled_count} fields on Greenhouse application form."
        }

    async def submit_form(self, page) -> bool:
        submit_btn = page.locator("input[type='submit']#submit_app, button[type='submit']#submit_app, input[type='submit'][value*='Submit']").first
        if await submit_btn.count() > 0:
            await submit_btn.click()
            return True
        return False
