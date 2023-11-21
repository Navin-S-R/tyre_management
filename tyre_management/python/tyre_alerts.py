import json
import frappe
import requests
from tyre_management.python.frontend_api import get_smart_tyre_data_bulk
import datetime
from itertools import groupby
from frappe.utils import (
	today
)
from twilio_integration.twilio_integration.doctype.whatsapp_message.whatsapp_message import WhatsAppMessage
from urllib.parse import quote

def send_preventive_maintenance_alert():
	vehicle_list=[]
	time_change_start=datetime.timedelta(hours=12)
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
					tyre_msg=f"Dear {vehicle_details.get('customer')},\n\nGreeting from Liquiconnect Team!\n\nFor your vehicle number {key}, the preventive maintenance was done on {today()}, the necessary information is as follows.\n\n"
					if alert_type:
						party_details["alert_type"] = alert_type
						tyre_serial_no_list=[]
						for row_value in value:
							tyre_msg += "Tire Serial Number: "+str(row_value.get('tyre_serial_no'))+"\n"
							tyre_msg += "Tire Pressure: "+str(row_value.get('Pres'))+"\n"
							tyre_msg += "Tire Temp: "+str(row_value.get('Temp'))+"\n"
							tyre_msg += "Nsd Value: "+str(row_value.get('nsd_value'))
							tyre_msg += "\n\n"
							tyre_serial_no_list.append(str(row_value.get('tyre_serial_no')))
						tyre_msg += "Thanks,\nLiquiconnect Team."
						if "WHATSAPP" in party_details["alert_type"] and party_details.get('whatsapp_number'):
								if party_details.get('whatsapp_number').startswith("+91"):
										receiver_whatsapp_no = party_details.get('whatsapp_number')
										receiver_whatsapp_no.replace(" ","")
								else:
									receiver_whatsapp_no = "+91"+party_details.get('whatsapp_number')
									receiver_whatsapp_no.replace(" ","")
								ref_doctype_actual="Vehicle Registration Certificate"
								ref_document_actual=key
								WhatsAppMessage.send_whatsapp_message(receiver_list=[receiver_whatsapp_no],message=tyre_msg,doctype=ref_doctype_actual,docname=ref_document_actual)
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