import frappe
import json
@frappe.whitelist()
def pull_realtime_data(**args):
	frappe.log_error(message = args, title = "JK Realtime data")
	args = json.loads(args)
	frappe.new_get({
		"doctype" : "Smart Tyre Realtime Data",
		"device_id" : args.get('DeviceId'),
		"device_date_time" : args.get('DeviceDateTime'),
		"ref_doctype" : "Vehicle Registration Certificate",
		"vehicle_no" : args.get('vehicleNo'),
		"erp_time_stamp" : frappe.utils.now(),
		"overall_response" : json.dumps(args,indent=4)
	}).insert(ignore_permissions=True)

	return {"response" : "Success"}
