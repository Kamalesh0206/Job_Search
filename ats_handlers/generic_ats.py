import logging
from typing import Dict, Any
from .base import BaseATSHandler

logger = logging.getLogger(__name__)

class GenericATSHandler(BaseATSHandler):
    def can_handle(self, url: str, content: str = "") -> bool:
        # Fallback handler for any page with form elements
        return True

    async def fill_form(self, page, cover_letter: str = "") -> Dict[str, Any]:
        filled_count = 0
        p = self.profile.personal
        links = self.profile.links

        inputs = page.locator("input, textarea")
        count = await inputs.count()

        for i in range(count):
            inp = inputs.nth(i)
            if not await inp.is_visible():
                continue

            inp_type = (await inp.get_attribute("type") or "text").lower()
            name = (await inp.get_attribute("name") or "").lower()
            elem_id = (await inp.get_attribute("id") or "").lower()
            placeholder = (await inp.get_attribute("placeholder") or "").lower()
            aria = (await inp.get_attribute("aria-label") or "").lower()

            combined = f"{name} {elem_id} {placeholder} {aria}"

            if inp_type in ["hidden", "submit", "button", "checkbox", "radio"]:
                continue

            # First Name
            if any(k in combined for k in ["first_name", "firstname", "given-name"]):
                await inp.fill(p.get("first_name", ""))
                filled_count += 1
            # Last Name
            elif any(k in combined for k in ["last_name", "lastname", "family-name"]):
                await inp.fill(p.get("last_name", ""))
                filled_count += 1
            # Full Name
            elif any(k in combined for k in ["full_name", "fullname", "your name"]) and not p.get("first_name"):
                await inp.fill(self.profile.get_full_name())
                filled_count += 1
            # Email
            elif "email" in combined or inp_type == "email":
                await inp.fill(p.get("email", ""))
                filled_count += 1
            # Phone
            elif "phone" in combined or "mobile" in combined or inp_type == "tel":
                await inp.fill(p.get("phone", ""))
                filled_count += 1
            # LinkedIn
            elif "linkedin" in combined:
                await inp.fill(links.get("linkedin", ""))
                filled_count += 1
            # GitHub
            elif "github" in combined:
                await inp.fill(links.get("github", ""))
                filled_count += 1
            # Website / Portfolio
            elif "portfolio" in combined or "website" in combined or "url" in combined:
                await inp.fill(links.get("portfolio") or links.get("website", ""))
                filled_count += 1
            # Cover letter textarea
            elif "cover" in combined or "letter" in combined or "message" in combined:
                if cover_letter:
                    await inp.fill(cover_letter)
                    filled_count += 1

        # File Upload for Resume
        resume_path = self.profile.get_resume_absolute_path()
        if resume_path and resume_path.exists():
            file_inputs = page.locator("input[type='file']")
            if await file_inputs.count() > 0:
                try:
                    await file_inputs.first.set_input_files(str(resume_path))
                    filled_count += 1
                except Exception as e:
                    logger.warning(f"Generic file upload failed: {e}")

        return {
            "success": True,
            "fields_filled": filled_count,
            "handler": "GenericATS",
            "notes": f"Filled {filled_count} fields using Generic ATS heuristic matcher."
        }

    async def submit_form(self, page) -> bool:
        submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Submit')").first
        if await submit_btn.count() > 0:
            await submit_btn.click()
            return True
        return False
