import frappe
@frappe.whitelist()
def pull_realtime_data(**args):
	print(args)
	frappe.log_error(message = args, title = "JK Realtime data")
	return {"response" : "Success"}
