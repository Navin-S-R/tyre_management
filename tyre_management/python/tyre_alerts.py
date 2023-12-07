import json
import frappe
import requests
from tyre_management.python.frontend_api import get_smart_tyre_data_bulk,get_tyres_need_service_nsd_based
import datetime
from itertools import groupby
from frappe.utils import (
	today
)
from twilio_integration.twilio_integration.doctype.whatsapp_message.whatsapp_message import WhatsAppMessage
from urllib.parse import quote

def send_preventive_maintenance_completion_alert():
	# The above code is retrieving a list of vehicles that require preventive maintenance within a
	# specific time range. It then retrieves the tire data for these vehicles and sends maintenance
	# alerts to the vehicle owners via WhatsApp. The code also updates the alert details for the
	# maintenance records in the database.
	vehicle_list=[]
	time_change_start=datetime.timedelta(hours=28)
	time_change_end=datetime.timedelta(hours=1)
	start_datetime=(datetime.datetime.now()-time_change_start)
	end_datetime=(datetime.datetime.now() - time_change_end)
	maintenance_alert_list = frappe.get_all("Tyre Maintenance",
								{
									"maintenance_type":"Preventive Maintenance",
									"time_stamp": ["between", [start_datetime, end_datetime]],
									"alert_details":["not in",["Preventive Maintenance"]],
									"docstatus":1
								},
								["name","customer","vehicle_no","serial_no"])
	if maintenance_alert_list:
		sorted_data = sorted(maintenance_alert_list, key=lambda x: x['vehicle_no'])
		grouped_data = {key: list(group) for key, group in groupby(sorted_data, key=lambda x: x['vehicle_no'])}
		for key, value in grouped_data.items():
			no_of_wheels = frappe.db.get_value("Vehicle Registration Certificate",{"name":key},"wheels")
			if no_of_wheels and no_of_wheels <= len(value):
				vehicle_list.append(key)
	if vehicle_list:
		res = get_smart_tyre_data_bulk(Vehicle_list=vehicle_list)
		if res and res.get('status') =='success' and res.get('res'):
			for key, value in res.get('res').items():
				vehicle_details=frappe.db.get_value("Vehicle Registration Certificate",{"name":key},['customer'],as_dict=True)
				if vehicle_details:
					party_details=frappe.db.get_value("Customer",{"name":vehicle_details.get('customer')},['mail_to_receive_alert','whatsapp_number','name'],as_dict=True)
					alert_type = frappe.get_all("Alert Type Multselect", {
							"parent": vehicle_details.get('customer'),
							"parentfield": "alert_type",
							"parenttype": "Customer"
						}, pluck="alert_type") or []
					if alert_type:
						party_details["alert_type"] = alert_type
						if "WHATSAPP" in party_details["alert_type"] and party_details.get('whatsapp_number'):
							if party_details.get('whatsapp_number').startswith("+91"):
									receiver_whatsapp_no = party_details.get('whatsapp_number')
									receiver_whatsapp_no.replace(" ","")
							else:
								receiver_whatsapp_no = "+91"+party_details.get('whatsapp_number')
								receiver_whatsapp_no.replace(" ","")
							ref_doctype_actual="Vehicle Registration Certificate"
							ref_document_actual=key

							tyre_serial_no_list=[]
							tyre_msg=f"Dear {vehicle_details.get('customer')},\n\nGreeting from Liquiconnect Team!\n\nFor your vehicle number {key}, the preventive maintenance was done on {today()}, the necessary information is as follows.\n\n"
							tyre_count=0
							nsd_value_details=[]
							tyre_health = ""
							for row_value in value:
								tyre_msg += "Tire Serial Number: "+str(row_value.get('tyre_serial_no'))+"\n"
								tyre_msg += "Tire Pressure: "+str(row_value.get('Pres'))+"\n"
								tyre_msg += "Tire Temp: "+str(row_value.get('Temp'))+"\n"
								if row_value.get('nsd_value') >= 20:
									tyre_health = "High"
								elif row_value.get('nsd_value') < 20 and row_value.get('nsd_value') >= 10:
									tyre_health = "Medium"
								elif row_value.get('nsd_value') < 10 and row_value.get('nsd_value') >= 5:
									tyre_health = "Low"
								elif row_value.get('nsd_value') <= 4:
									tyre_health = "Needs change"
								tyre_msg += "Tyre health: "+ tyre_health
								tyre_msg += "\n\n"
								tyre_serial_no_list.append(str(row_value.get('tyre_serial_no')))
								tyre_count+=1
								if row_value.get('nsd_value') and float(row_value.get('nsd_value')) <= 4:
									nsd_value_details.append(
										{
											"serial_no" : row_value.get('tyre_serial_no'),
											"nsd_value" : row_value.get('nsd_value')
										}
									)
								if tyre_count == 8:
									tyre_count = 0
									tyre_msg += "Thanks,\nLiquiconnect Team."
									send_whatsapp_msg(receiver_whatsapp_no=receiver_whatsapp_no,
										tyre_msg=tyre_msg,
										ref_doctype_actual=ref_doctype_actual,
										ref_document_actual=ref_document_actual
									)
									tyre_msg=f"Dear {vehicle_details.get('customer')},\n\nGreeting from Liquiconnect Team!\n\nFor your vehicle number {key}, the preventive maintenance was done on {today()}, the necessary information is as follows.\n\n"
							if tyre_count>0:
								tyre_msg += "Thanks,\nLiquiconnect Team."
								send_whatsapp_msg(receiver_whatsapp_no=receiver_whatsapp_no,
										tyre_msg=tyre_msg,
										ref_doctype_actual=ref_doctype_actual,
										ref_document_actual=ref_document_actual
								)
							tyre_msg=None
							if nsd_value_details:
								nsd_count=0
								nsd_value_msg=f"Dear {vehicle_details.get('customer')},\n\nGreeting from Liquiconnect Team!\n\nFor your vehicle number {key}, the below tyre needs to be changed.\n\n"
								for row in nsd_value_details:
									nsd_value_msg+= "Tire Serial Number: "+row.get('serial_no')+"\n"
									nsd_value_msg+= "Nsd Value: "+row.get('nsd_value')
									nsd_value_msg += "\n\n"
									nsd_count += 1
									if nsd_count == 11:
										nsd_count = 0
										nsd_value_msg += "Thanks,\nLiquiconnect Team."
										send_whatsapp_msg(receiver_whatsapp_no=receiver_whatsapp_no,
											tyre_msg=nsd_value_msg,
											ref_doctype_actual=ref_doctype_actual,
											ref_document_actual=ref_document_actual
										)
										nsd_value_msg=f"Dear {vehicle_details.get('customer')},\n\nGreeting from Liquiconnect Team!\n\nFor your vehicle number {key}, the below tyre needs to be changed.\n\n"
								if nsd_count>0:
									nsd_value_msg += "Thanks,\nLiquiconnect Team."
									send_whatsapp_msg(receiver_whatsapp_no=receiver_whatsapp_no,
											tyre_msg=nsd_value_msg,
											ref_doctype_actual=ref_doctype_actual,
											ref_document_actual=ref_document_actual
									)
							vehicle_costing = frappe.get_all("Tyre Maintenance",
													{
														"maintenance_type":"Preventive Maintenance",
														"time_stamp": ["between", [start_datetime, end_datetime]],
														"alert_details":["not in",["Preventive Maintenance"]],
														"serial_no" : ["in",tyre_serial_no_list],
														"vehicle_no" : key,
														"docstatus":1
													},
													["name","customer","vehicle_no","serial_no","cost"])
							if vehicle_costing:
								cost_count=0
								cost_value_msg=f"Dear {vehicle_details.get('customer')},\n\nGreeting from Liquiconnect Team!\n\nFor your vehicle number {key}, the preventive maintenance was done on {today()}, the costing information is as follows.\n\n"
								total_cost = 0
								for row in nsd_value_details:
									cost_value_msg+= "Tire Serial Number: "+row.get('serial_no')+"\n"
									cost_value_msg+= "Cost: "+row.get('cost')
									cost_value_msg += "\n\n"
									total_cost += row.get('cost')
									cost_count += 1
									if cost_count == 10:
										cost_count = 0
										cost_value_msg += f"Total cost for the above tyres : {total_cost} \n\n"
										cost_value_msg += "Thanks,\nLiquiconnect Team."
										send_whatsapp_msg(receiver_whatsapp_no=receiver_whatsapp_no,
											tyre_msg=cost_value_msg,
											ref_doctype_actual=ref_doctype_actual,
											ref_document_actual=ref_document_actual
										)
										cost_value_msg=f"Dear {vehicle_details.get('customer')},\n\nGreeting from Liquiconnect Team!\n\nFor your vehicle number {key}, the preventive maintenance was done on {today()}, the costing information is as follows.\n\n"
										total_cost = 0
								if cost_count>0:
									cost_value_msg += f"Total cost for the above tyres : {total_cost} \n\n"
									cost_value_msg += "Thanks,\nLiquiconnect Team."
									send_whatsapp_msg(receiver_whatsapp_no=receiver_whatsapp_no,
											tyre_msg=cost_value_msg,
											ref_doctype_actual=ref_doctype_actual,
											ref_document_actual=ref_document_actual
									)
							if tyre_serial_no_list:
								serial_no_list="', '".join(tyre_serial_no_list)
								frappe.db.sql("""
									UPDATE `tabTyre Maintenance`
										SET alert_details = 'Preventive Maintenance'
											WHERE
												maintenance_type='Preventive Maintenance'
												AND docstatus=1
												AND time_stamp BETWEEN '{0}' AND '{1}'
												AND serial_no IN ('{2}')
								""".format(start_datetime, end_datetime, serial_no_list))

#send_alert_for_preventive_maintenance need for these vehicles
def send_alert_for_preventive_maintenance_needed():
	"""
	The function sends an alert for preventive maintenance needed for vehicles that have traveled more
	than 10,000 kms without a checkup.
	"""
	customer_list=frappe.get_all("Vehicle Tire Position", pluck="customer", distinct=True)
	if customer_list:
		for customer in customer_list:
			response=get_tyres_need_service_nsd_based(customer)
			if response and isinstance(response, list):
				vehicle_with_10k_kms = [item['vehicle_no'] for item in response if item['kms_travelled_without_checkup'] > 10000 and item['last_alert_sent'] != 'Maintenance Needed']

#Send Whatsapp message
def send_whatsapp_msg(receiver_whatsapp_no,tyre_msg,ref_doctype_actual,ref_document_actual):
	WhatsAppMessage.send_whatsapp_message(receiver_list=[receiver_whatsapp_no],message=tyre_msg,doctype=ref_doctype_actual,docname=ref_document_actual)