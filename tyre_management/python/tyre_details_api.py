import frappe
@frappe.whitelist()
def pull_realtime_data(args):
	print(args)