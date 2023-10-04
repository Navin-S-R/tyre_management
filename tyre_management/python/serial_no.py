import frappe

def validate_serial_no(doc,event):
	if doc.item_group.lower() in ['tires','tyres','tire','tyre']:
		if not frappe.db.exists("Tyre Serial No",{"name":doc.serial_no}):
			frappe.get_doc({
				"doctype":"Tyre Serial No",
				"serial_no" : doc.serial_no,
				"item_code" : doc.item_code
			}).insert()
