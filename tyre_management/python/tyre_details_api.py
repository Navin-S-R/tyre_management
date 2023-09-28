import frappe
@frappe.whitelist()
def pull_realtime_data(**args):
	print(args)
	#frappe.log_error(args)
	return {"response" : "Success"}