from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
def user_customization():
	user_custom_fields()
	user_property_setter()

def user_custom_fields():
	custom_fields = {
		"User":[
			dict(
				fieldname="driving_vehicle_no",
				fieldtype="Link",
				label="Driving Vehicle No",
				options="Vehicle Registration Certificate",
				insert_after="desk_theme"
			)
		]
	}
	create_custom_fields(custom_fields)
def user_property_setter():
	pass