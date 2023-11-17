import frappe
from frappe.desk.query_report import build_xlsx_data
from frappe.utils.xlsxutils import make_xlsx
from frappe.sessions import Session, clear_sessions, delete_session

@frappe.whitelist(allow_guest = True)
def generate_excel_report():
	frappe.set_user("Administrator")
	sheet_no = 0
	report_datas = []
	
	report = frappe.get_doc("Report", "Fuel Billing")
	columns, data = report.get_data(
		limit=500,
		user="Administrator",
		filters={},
		as_dict=True,
		ignore_prepared_report=True,
	)

	# Add serial numbers
	columns.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
	for i in range(len(data)):
		data[i]["idx"] = i + 1

	report_data = frappe._dict()
	report_data["columns"] = columns
	report_data["result"] = data

	if data:
		xlsx_data, column_widths = build_xlsx_data(
			columns, report_data, [], 1, ignore_visible_idx=True
		)
		sheet_no += 1
		report_datas.append({
			"xlsx_data": xlsx_data,
			"sheet_name": 'fuel_billing',
			"column_widths": column_widths,
			"sheet_no": sheet_no
		})


	xlsx_file = make_xlsx(report_datas,"Hello")
	frappe.response.clear()
	frappe.response['contenttype'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
	frappe.response['filename'] = f"Fuel_Billing_report.xlsx"
	frappe.response['filecontent'] = xlsx_file
	frappe.response['type'] = 'download'
	delete_session('Administrator', reason="Session Expired")
