import frappe

#Get Customer purchased tyre details
@frappe.whitelist()
def get_customer_purchase_type_details(customer):
	tyre_details=[]
	serial_no_list = frappe.get_all("Serial No",{"item_group":"Tires","status":"Delivered","customer":customer},pluck="name")
	for serial_no in serial_no_list:
		serial_no_doc = frappe.get_doc("Serial No",serial_no)
		data={
			"purchase_date": serial_no_doc.purchase_date,
			"delivery_time" : serial_no_doc.delivery_time,
			"serial_no" : serial_no_doc.name,
			"purchase_rate" : serial_no_doc.purchase_rate,
			"selling_rate" : serial_no_doc.invoiced_rate,
			"brand" : serial_no_doc.brand,
			"tyre_size" : serial_no_doc.tyre_size,
			"cost_per_kms" : 0,
			"operational_date" : None,
			"operational_end_date" : None,
			"scarped_date" : None,
			"preventive_maintenance":[],
			"breakdown_cost":[],
			"cummulative_preventive_maintenance_cost" : 0,
			"cummulative_breakdown_cost":0,
			"scarped_cost":0,
			"total_cummulative_cost":0,
		}
		data['vehicle_no'] = serial_no_doc.vehicle_no
		data['operational_date'] = serial_no_doc.installed_datetime
		if serial_no_doc.tyre_status == "Installed":
			data['tyre_status'] = serial_no_doc.tyre_status
			tyre_position_doc = frappe.get_doc("Vehicle Tire Position",{"name":serial_no_doc.vehicle_tire_position})
			serial_no_fields = [
				"front_left_1",
				"front_right_1",
				"middle_left_1",
				"middle_right_1",
				"middle_left_2",
				"middle_right_2",
				"middle_left_3",
				"middle_right_3",
				"middle_left_4",
				"middle_right_4",
				"rear_left_1",
				"rear_right_1",
				"rear_left_2",
				"rear_right_2",
				"rear_left_3",
				"rear_right_3",
				"rear_left_4",
				"rear_right_4"
			]
			for tyre_position in serial_no_fields:
				if serial_no_doc.name == tyre_position_doc.get(tyre_position):
					data['tyre_position'] = tyre_position.replace("_", " ").capitalize()
		elif serial_no_doc.tyre_status == "Operation Ended":
			data['tyre_status'] = serial_no_doc.tyre_status
			data['operational_end_date'] = serial_no_doc.operational_end_date
		elif serial_no_doc.tyre_status == "Scarped":
			data['tyre_status'] = serial_no_doc.tyre_status
			data['scarped_date'] = serial_no_doc.scarped_datetime
		else:
			if serial_no_doc.delivery_document_no:
				data['tyre_status'] = "Item Delivered To Customer"
			else:
				data['tyre_status'] = "In Company Warehouse"
				data["tyre_location"] = serial_no_doc.warehouse

		breakdown_cost=frappe.get_all("Tyre Maintenance",{"serial_no":serial_no_doc.name,"maintenance_type":"Breakdown"},['time_stamp','vehicle_no','customer','vehicle_tire_position','maintenance_type','serial_no','tire_position','cost'])
		cost_breakdown_values = [entry['cost'] for entry in breakdown_cost]
		cummulative_breakdown_cost = sum(cost_breakdown_values)
		data['breakdown_cost'] = breakdown_cost
		data['cummulative_breakdown_cost'] = cummulative_breakdown_cost

		preventive_maintenance=frappe.get_all("Tyre Maintenance",{"serial_no":serial_no_doc.name,"maintenance_type":"Preventive Maintenance"},['time_stamp','vehicle_no','customer','vehicle_tire_position','maintenance_type','serial_no','tire_position','cost'])
		cost_preventive_maintenance_values = [entry['cost'] for entry in preventive_maintenance]
		cummulative_preventive_maintenance_cost = sum(cost_preventive_maintenance_values)
		data['cummulative_preventive_maintenance_cost'] = cummulative_preventive_maintenance_cost

		data['preventive_maintenance'] = preventive_maintenance

		scarped_cost = frappe.db.get_value("Scarp Tyre",{'serial_no':serial_no},'cost') or 0
		data['scarped_cost']=scarped_cost
		data['total_cummulative_cost'] = cummulative_preventive_maintenance_cost+cummulative_breakdown_cost+scarped_cost
		tyre_details.append(data)

	return tyre_details
