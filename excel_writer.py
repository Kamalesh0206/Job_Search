from pathlib import Path
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.datavalidation import DataValidation

HEADERS = [
    "ID", "Found Date", "Posted Date", "Role Category", "Job Title",
    "Company", "Location", "Source", "Job URL", "Status", "Fingerprint"
]

def _create(path: Path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Jobs"
    ws.append(HEADERS)

    header_fill = PatternFill("solid", fgColor="1F4E78")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    widths = {
        "A": 8, "B": 13, "C": 16, "D": 28, "E": 42,
        "F": 28, "G": 24, "H": 18, "I": 55, "J": 14, "K": 18
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = "A1:K1"

    dv = DataValidation(type="list", formula1='"New,Review,Applied,Interview,Rejected,Offer,Skip"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add("J2:J5000")

    wb.save(path)

def load_existing_fingerprints(path: Path):
    if not path.exists():
        _create(path)
        return set()
    wb = load_workbook(path, read_only=True)
    ws = wb["Jobs"]
    fps = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        if len(row) >= 11 and row[10]:
            fps.add(str(row[10]))
    wb.close()
    return fps

def append_jobs(path: Path, rows):
    if not path.exists():
        _create(path)

    wb = load_workbook(path)
    ws = wb["Jobs"]
    start_id = ws.max_row

    for i, item in enumerate(rows, start=start_id):
        ws.append([
            i,
            item["found_date"],
            item["posted_date"],
            item["role_category"],
            item["title"],
            item["company"],
            item["location"],
            item["source"],
            item["url"],
            item["status"],
            item["fingerprint"],
        ])

    if ws.max_row >= 2:
        # Recreate/expand the Excel table.
        if "JobsTable" in ws.tables:
            del ws.tables["JobsTable"]
        tab = Table(displayName="JobsTable", ref=f"A1:K{ws.max_row}")
        style = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        tab.tableStyleInfo = style
        ws.add_table(tab)

    wb.save(path)

def load_jobs_by_status(path: Path, target_statuses=None):
    if not path.exists():
        return []
    target_statuses = target_statuses or ["New", "Review"]
    wb = load_workbook(path, read_only=True)
    ws = wb["Jobs"]
    jobs = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or len(row) < 10:
            continue
        job_id, found_date, posted_date, role_category, title, company, location, source, url, status = row[:10]
        fp = row[10] if len(row) >= 11 else ""
        if status in target_statuses:
            jobs.append({
                "id": job_id,
                "found_date": found_date,
                "posted_date": posted_date,
                "role_category": role_category,
                "title": title,
                "company": company,
                "location": location,
                "source": source,
                "url": url,
                "status": status,
                "fingerprint": fp
            })
    wb.close()
    return jobs

def update_job_status(path: Path, identifier, new_status: str) -> bool:
    if not path.exists():
        return False
    wb = load_workbook(path)
    ws = wb["Jobs"]
    updated = False
    for row in ws.iter_rows(min_row=2):
        cell_id = row[0].value
        cell_fp = row[10].value if len(row) >= 11 else None
        if str(cell_id) == str(identifier) or (cell_fp and str(cell_fp) == str(identifier)):
            row[9].value = new_status  # Status column (0-indexed 9 = Column J)
            updated = True
            break
    if updated:
        wb.save(path)
    wb.close()
    return updated

