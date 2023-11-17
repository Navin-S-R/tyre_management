import frappe
from datetime import datetime
import requests
import json


from tyre_management.tyre_management.doctype.vehicle_tire_position.vehicle_tire_position import get_vehicle_tyre_positions

#Get Customer purchased tyre details
@frappe.whitelist()
def get_customer_purchase_type_details(customer,filter_serial_no=None,filter_is_smart_tyre=None,filter_vehicle_no=None):
	#Filters
	serial_doc_filters={
		"customer":customer
	}
	if filter_serial_no:
		serial_doc_filters['name'] = filter_serial_no
	if filter_is_smart_tyre == 0 or filter_is_smart_tyre == 1:
		serial_doc_filters['is_smart_tyre'] = filter_is_smart_tyre
	if filter_vehicle_no:
		serial_doc_filters['vehicle_no'] = filter_vehicle_no
	
	#Get Details
	tyre_details=[]
	serial_no_list = frappe.get_all("Tyre Serial No",serial_doc_filters,pluck="name")
	if not serial_no_list:
		return "No Data Found"
	for serial_no in serial_no_list:
		serial_no_doc = frappe.get_doc("Tyre Serial No",serial_no)
		data={
			"erp_serial_no":serial_no_doc.erp_serial_no,
			"is_smart_tyre" : serial_no_doc.is_smart_tyre,
			"purchase_date": serial_no_doc.purchase_date,
			"purchase_time" : serial_no_doc.purchase_time,
			"delivery_date" : serial_no_doc.delivery_date,
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
			"duration_in_operation" : 0,
			"nsd_value" : frappe.db.get_value("Tyre Maintenance",{"serial_no": serial_no, "maintenance_type":['in',["Preventive Maintenance"]], "docstatus": 1},'nsd_value'),
			"kilometer_driven":serial_no_doc.kilometer_driven,
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

		breakdown_cost=frappe.get_all("Tyre Maintenance",{"serial_no":serial_no_doc.name,"maintenance_type":"Breakdown","docstatus":1},['time_stamp','vehicle_no','customer','vehicle_tire_position','maintenance_type','serial_no','tire_position','cost'])
		cost_breakdown_values = [entry['cost'] for entry in breakdown_cost]
		cummulative_breakdown_cost = sum(cost_breakdown_values)
		data['breakdown_cost'] = breakdown_cost
		data['cummulative_breakdown_cost'] = cummulative_breakdown_cost

		preventive_maintenance=frappe.get_all("Tyre Maintenance",{"serial_no":serial_no_doc.name,"maintenance_type":['in',["Preventive Maintenance"]],"docstatus":1},['time_stamp','vehicle_no','customer','vehicle_tire_position','maintenance_type','serial_no','tire_position','cost'])
		cost_preventive_maintenance_values = [entry['cost'] for entry in preventive_maintenance]
		cummulative_preventive_maintenance_cost = sum(cost_preventive_maintenance_values)
		data['cummulative_preventive_maintenance_cost'] = cummulative_preventive_maintenance_cost

		data['preventive_maintenance'] = preventive_maintenance

		scarped_cost=frappe.db.get_value("Scarp Tyre",{'serial_no':serial_no,"docstatus":1},'cost') or 0
		data['scarped_cost'] = scarped_cost
		data['total_cummulative_cost'] = serial_no_doc.invoiced_rate + cummulative_breakdown_cost + cummulative_preventive_maintenance_cost - scarped_cost

		if data.get('operational_date'):
			to_date = data.get('operational_end_date') if data.get('operational_end_date') else datetime.now()
			time_difference = to_date-data.get('operational_date')
			data['duration_in_operation'] = time_difference.days
		if data['total_cummulative_cost'] and serial_no_doc.kilometer_driven:
			data['cost_per_kms'] = data['total_cummulative_cost'] / serial_no_doc.kilometer_driven
		tyre_details.append(data)

	return tyre_details

#Get Customer Linked Tyre
@frappe.whitelist()
def get_customer_linked_tyre_serial_no(customer):
	serial_no_list = frappe.get_all("Tyre Serial No",{"status":['in',["Delivered","Active","Inactive"]],"customer":customer},pluck="name")
	return serial_no_list

#Get Customer Linked Vehicle
@frappe.whitelist()
def get_customer_linked_vehicle(customer,doctype):
	if doctype == "Vehicle Registration Certificate":
		vehicle_list = frappe.get_all("Vehicle Registration Certificate",{"customer":customer,"disabled":0},pluck="name")
	## To use core vehicle doctype
	#elif doctype == "Vehicle":
	#	vehicle_list = frappe.get_all("Vehicle",{"customer",customer},"name")
	return vehicle_list

#Get Details for Tyre Cards:
@frappe.whitelist()
def get_fleet_tyre_details_card(customer):
	data={
			"avgCost_Km" : 0,
			"avgMaintainceCost" : 0,
			"avgBreakdownCost":0,
			"no_of_vehicles":0,
			"no_of_smart_tyres":0,
			"no_of_regular_tyres":0,
			"no_of_vehicles_with_regular_tyre":0,
			"no_of_vehicles_with_smart_tyre":0,
			"no_of_tyres_need_service":0,
			"no_of_scarped_tyres":0,
			"vehicles_with_regular_tyre" : [],
			"vehicles_with_smart_tyre" : []
		}
	data['no_of_vehicles'] = len(frappe.get_all("Vehicle Registration Certificate",{"customer":customer,"disabled":0},pluck="name"))
 
	#smart_tyre_list
	smart_tyre_list = frappe.get_all("Tyre Serial No",{"status":['in',["Delivered","Active","Inactive",None]],
																"tyre_status":["not in",["Scarped"]],"customer":customer,
																"is_smart_tyre":1
																},
													pluck="name")
	data["no_of_smart_tyres"] = len(smart_tyre_list)
	#regular_tyre_list
	regular_tyre_list = frappe.get_all("Tyre Serial No",{"status":['in',["Delivered","Active","Inactive",None]],
																"tyre_status":["not in",["Scarped"]],"customer":customer,
																"is_smart_tyre":0
																},
													pluck="name")
	data["no_of_regular_tyres"] = len(regular_tyre_list)
 
	#scarped_tyre_list
	scarped_tyre_list = frappe.get_all("Tyre Serial No",{"status":['in',["Delivered","Active","Inactive",None]],
																"tyre_status":"Scarped","customer":customer,
																},
													pluck="name")
	data["no_of_scarped_tyres"] = len(scarped_tyre_list)
	scarped_cost = 0
	if scarped_tyre_list:
		scarped_tyre_details = frappe.get_all("Scarp Tyre",{"serial_no":['in',scarped_tyre_list],"docstatus":1},["cost"])
		scarped_cost = sum(item['cost'] for item in scarped_tyre_details)
	data['total_scarped_tyre_cost'] = scarped_cost
	active_tyres = smart_tyre_list + regular_tyre_list
	no_of_active_tyres = len(active_tyres)

	#Get Maintaince Cost
	maintaince_cost_list = frappe.get_all("Tyre Maintenance",{"serial_no":['in',active_tyres],"maintenance_type":['in',["Preventive Maintenance"]],"docstatus":1},pluck='cost')
	maintaince_cost = sum(maintaince_cost_list) if maintaince_cost_list else 0
	data['total_maintenance_cost'] = maintaince_cost
	data['avgMaintainceCost'] = maintaince_cost/no_of_active_tyres if no_of_active_tyres else 0
 
	#Get Break Down Cost Cost
	breakdown_cost_list = frappe.get_all("Tyre Maintenance",{"serial_no":['in',active_tyres],"maintenance_type":"Breakdown","docstatus":1},pluck='cost')
	breakdown_cost = sum(breakdown_cost_list) if breakdown_cost_list else 0
	data['total_breakdown_cost'] = breakdown_cost
	data['avgBreakdownCost'] = breakdown_cost/no_of_active_tyres if no_of_active_tyres else 0
 
	#Get avgCost_Km
	kms_driven_and_rate_details=frappe.get_all("Tyre Serial No",{"name":['in',active_tyres]},["kilometer_driven","invoiced_rate"])
	total_kilometer_driven = sum(item['kilometer_driven'] for item in kms_driven_and_rate_details)
	total_cost = sum(item['invoiced_rate'] for item in kms_driven_and_rate_details)
	if total_kilometer_driven:
		data['avgCost_Km'] = (maintaince_cost+breakdown_cost)/total_kilometer_driven
	else:
		data['avgCost_Km'] = maintaince_cost+breakdown_cost
	
	#vehicles_with_regular_tyre
	vehicles_with_regular_tyre = frappe.get_all("Tyre Serial No",{"name":['in',regular_tyre_list],
																	"vehicle_no":["not in",None]},
														pluck="vehicle_no",distinct=True)
	data['vehicles_with_regular_tyre'] = vehicles_with_regular_tyre
	data['no_of_vehicles_with_regular_tyre'] = len(vehicles_with_regular_tyre)
	
	#vehicles_with_smart_tyre
	vehicles_with_smart_tyre = frappe.get_all("Tyre Serial No",{"name":['in',smart_tyre_list],
																	"vehicle_no":["not in",None]},
														pluck="vehicle_no",distinct=True)
	# vehicles_with_only_smart_tyre
	vehicles_with_only_smart_tyre = [x for x in vehicles_with_smart_tyre if x not in vehicles_with_regular_tyre]
	data['vehicles_with_smart_tyre'] = vehicles_with_only_smart_tyre
	data['no_of_vehicles_with_smart_tyre'] = len(vehicles_with_only_smart_tyre)
	
	return data

#Get Service Required Tyres Based on NSD
@frappe.whitelist()
def get_tyres_need_service_nsd_based(customer):
	linked_vehicles=get_customer_linked_vehicle(customer,"Vehicle Registration Certificate")
	final_data=[]
	if linked_vehicles:
		url = "http://service.lnder.in/api/method/tyre_management_connector.tyre_management_connector.doctype.smart_tyre_realtime_data.smart_tyre_realtime_data.get_smart_tyre_data_bulk"
		payload = json.dumps({
		"filters": {
			"vehicle_no": linked_vehicles,
			"sort": "DESC"
		},
			"odometer_value" : True
		})
		headers = {
			'Authorization': 'token 4567d5a4c58d5ba:50f7dcc70df884f',
			'Content-Type': 'application/json'
		}
		response = requests.request("POST", url, headers=headers, data=payload)
		if response.ok:
			response=response.json().get('message')
			for key,val in response.items():
				for row in val:
					if row.get('current_odometer_value'):
						current_odometer_value = row.get('current_odometer_value')
					if row.get('tyre_serial_no'):
						tyre_serial_details=frappe.db.get_value("Tyre Serial No",{"name": row.get('tyre_serial_no')},['odometer_value_at_installation'],as_dict=True)
						tyre_maintenance_details = frappe.db.get_value("Tyre Maintenance",{"serial_no": row.get('tyre_serial_no'),
											"maintenance_type":['in',["Preventive Maintenance"]],"docstatus":1},
								['vehicle_odometer_value_at_service','nsd_value'],as_dict=True)
						if tyre_maintenance_details and tyre_maintenance_details.get('vehicle_odometer_value_at_service'):
							kms_driven_without_checkup=current_odometer_value-tyre_maintenance_details.get('vehicle_odometer_value_at_service')
							nsd_value = tyre_maintenance_details.get('nsd_value') or 0
						else:
							kms_driven_without_checkup=current_odometer_value-tyre_serial_details.get('odometer_value_at_installation')
							nsd_value = 0
						if ((kms_driven_without_checkup and kms_driven_without_checkup >= 10000) or
							row.get('min_tyre_temperature')>=row.get('Temp') or row.get('max_tyre_temperature')<=row.get('Temp') or 
							row.get('min_tyre_pressure')>=row.get('Pres') or row.get('max_tyre_pressure')<=row.get('Pres')) or nsd_value<=4:
							final_data.append({
								'vehicle_no' : key,
								'tyre_serial_no' : row.get('tyre_serial_no'),
								'tyre_pressure' : row.get('Pres'),
								'tyre_temperature' : row.get('Temp'),
								'nsd_value' : nsd_value,
								'kms_travelled_without_checkup' : kms_driven_without_checkup,
								'total_tyre_mileage' : current_odometer_value-tyre_serial_details.get('odometer_value_at_installation')
							})
			return final_data
		else:
			return response.raise_for_status()
	else:
		return "No Vehicle Linked"

def get_smart_tyre_data_bulk(Vehicle_list=None,odometer_value=False):
	url = "http://service.lnder.in/api/method/tyre_management_connector.tyre_management_connector.doctype.smart_tyre_realtime_data.smart_tyre_realtime_data.get_smart_tyre_data_bulk"
	filters={
		"sort": "DESC"
	}
	if Vehicle_list:
		filters["vehicle_no"] = Vehicle_list
	payload = json.dumps({
		"filters": filters,
		"odometer_value": False
	})
	headers = {
		'Authorization': 'token 4567d5a4c58d5ba:50f7dcc70df884f',
		'Content-Type': 'application/json'
	}
	response = requests.request("POST", url, headers=headers, data=payload)
	if response.ok:
		response=response.json().get('message')
		return {
			"res":response,
			"status":'success'
		}
	else:
		return {
			"res":response.raise_for_status(),
			"status": 'failure'
		}