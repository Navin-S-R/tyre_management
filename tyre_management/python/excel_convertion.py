import frappe
from frappe.desk.query_report import build_xlsx_data
from frappe.utils.xlsxutils import make_xlsx
from frappe.sessions import delete_session

@frappe.whitelist(allow_guest=True)
def generate_excel_report():
	frappe.set_user("Administrator")
	# Fetch the report
	report = frappe.get_doc("Report", "Fuel Billing")
	# Get report data
	columns, data = report.get_data(
		limit=500,
		user="Administrator",
		filters={},
		as_dict=True,
		ignore_prepared_report=True,
	)

	columns.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
	for i in range(len(data)):
		data[i]["idx"] = i + 1
	report_data = frappe._dict()
	report_data["columns"] = columns
	report_data["result"] = data
	if data:
		xlsx_data, column_widths = build_xlsx_data(columns, report_data, [], 1, ignore_visible_idx=True)
		xlsx_file=make_xlsx(data=xlsx_data,sheet_name='Fuel Billing',column_widths=column_widths)
		data = xlsx_file.getvalue()
		frappe.local.response.filecontent = data
		frappe.local.response.type = "download"
		frappe.local.response.filename = 'fuel.xlsx'

