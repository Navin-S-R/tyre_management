# Copyright (c) 2023, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from datetime import datetime
import json
from tyre_management.python.tyre_alerts import send_whatsapp_msg
from tyre_management.python.frontend_api import get_location_for_lat_lng,get_current_vehicle_location,get_unprocessed_not_moving_vehicles
from twilio_integration.twilio_integration.doctype.whatsapp_message.whatsapp_message import WhatsAppMessage
from urllib.parse import quote

class VehicleTrackingLog(Document):
	def validate(self):
		previous_doc=frappe.db.get_value("Vehicle Tracking Log",{"vehicle_no":self.vehicle_no,"docstatus":0,"name":["not in",[self.name]]},"name")
		if previous_doc:
			frappe.throw(_(f"Previous Log is not yet closed, <a href='{frappe.utils.get_url()}/vehicle-tracking-log?name={previous_doc}'>{ _('Update the previous progress')}</a>"))
		if not self.timestamp:
			self.timestamp = frappe.utils.now()
		if not self.start_time:
			self.start_time = frappe.utils.now()
		if self.docstatus == 0 and self.issue_based_on=="Breakdown" and self.status in ["Breakdown","Work in Progress"]:
			vehicle_details=frappe.db.get_value(self.ref_doctype,{"name":self.vehicle_no},['customer'],as_dict=True)
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
						if receiver_whatsapp_no:
							if self.status=="Breakdown" and self.alert_details != "Breakdown" and self.time_spent_on in ['Tyre','Engine']:
								if self.location_details:
									if isinstance(self.location_details, str):
										location_details = json.loads(self.location_details)
										if isinstance(self.location_details, str):
											self.location_details = json.dumps(self.location_details)
									else:
										location_details = self.location_details

									location=get_location_for_lat_lng(lat=location_details.get('lat'),lng=location_details.get('lng'))
									if location:
										location=location.get('display_name')
									else:
										location=f"Lat : {location_details.get('lat')} - Lng: {location_details.get('lng')}"
								else:
									location="Exact Location Not Found"
								alert_msg=f"Dear {self.customer},\n\nGreeting from Liquiconnect Team!\n\nyour vehicle number {self.vehicle_no} had a breakdown at {location}.\n\n The reason for the breakdown is {self.reason_for_breakdown}.\n\nThanks,\nLiquiconnect Team."
								send_whatsapp_msg(receiver_whatsapp_no,alert_msg,self.ref_doctype,self.vehicle_no)
								self.alert_details='Breakdown'
							if self.status=="Work in Progress" and self.alert_details != "Work in Progress" and self.time_spent_on in ['Tyre','Engine']:
								location_result=get_current_vehicle_location([self.vehicle_no])
								if (location_result and
										location_result.get('status') == 'success' and
										location_result.get('res') and
										location_result.get('res').get(self.vehicle_no) and
										location_result.get('res').get(self.vehicle_no).get('display_name')):

									location=location_result.get('res').get(self.vehicle_no).get('display_name')
								else:
									location="Exact Location Not Found"
								alert_msg=f"Dear {self.customer},\n\nGreeting from Liquiconnect Team!\n\nyour vehicle number {self.vehicle_no} had a breakdown and this complaint adhered to {self.workshop} at {location}.\n\nThanks,\nLiquiconnect Team."
								send_whatsapp_msg(receiver_whatsapp_no,alert_msg,self.doctype,self.name)
								self.alert_details='Work in Progress'

						if self.location_details:
							if isinstance(self.location_details, dict):
								self.location_details = json.dumps(self.location_details)


		#['Layover','FasTag','Accident','Fuel'] Direct submission
		if self.issue_based_on in ['Layover','FasTag','Accident','Fuel']:
			if not self.end_time:
				self.end_time = frappe.utils.now()
			self.docstatus=1
			self.status = "Completed"
			if self.start_time and self.end_time:
				if isinstance(self.start_time, str):
					self.start_time = datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S.%f")
				if isinstance(self.end_time, str):
					self.end_time = datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S.%f")
				self.duration_in_mins = (self.end_time - self.start_time).total_seconds() / 60

	#On Submit
	def on_submit(self):
		self.status = "Completed"
		if not self.end_time:
			self.end_time = frappe.utils.now()
		if self.start_time and self.end_time:
			if isinstance(self.start_time, str):
				self.start_time = datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S.%f")
			if isinstance(self.end_time, str):
				self.end_time = datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S.%f")
			self.duration_in_mins = (self.end_time - self.start_time).total_seconds() / 60

		if self.issue_based_on=="Breakdown" and self.status=="Completed":
			vehicle_details=frappe.db.get_value(self.ref_doctype,{"name":self.vehicle_no},['customer'],as_dict=True)
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
						if receiver_whatsapp_no:
							alert_msg=f"Dear {self.customer},\n\nGreeting from Liquiconnect Team!\n\nyour vehicle number {self.vehicle_no} had a breakdown and it was resolved.\n\nThe cost involved to resolve : {self.cost_involved}\n\nThanks,\nLiquiconnect Team."
							send_whatsapp_msg(receiver_whatsapp_no,alert_msg,self.doctype,self.name)

# Send Initial Request MSG
def send_whatsapp_msg_to_driver(threshold_minutes=20):
	response=get_unprocessed_not_moving_vehicles(threshold_minutes)
	if isinstance(response, list):
		for row in response:
			if row.get('driver_mobile'):
				if row.get('driver_mobile').startswith("+91"):
						receiver_whatsapp_no = row.get('driver_mobile')
						receiver_whatsapp_no.replace(" ","")
				else:
					receiver_whatsapp_no = "+91"+row.get('driver_mobile')
					receiver_whatsapp_no.replace(" ","")
				msg = f"Dear {row.get('driver_name')},\n\nGreeting from Liquiconnect Team!\n\nYour vehicle {row.get('vehicle_no')} is standing in the same place for about {threshold_minutes} minutes,\n\nPlease report the issue on the below link.\n\n"
				msg+=f"{frappe.utils.get_url()}/vehicle-tracking-log?new=1&&vehicle_no={row.get('vehicle_no')}"
				if row.get('geo_location'):
					msg+=f"&&location_details={quote(row.get('geo_location'))}"
				msg+="\n\nThanks,\nLiquiconnect Team."
				print(msg)
				WhatsAppMessage.send_whatsapp_message(receiver_list=[receiver_whatsapp_no],message=msg,doctype="Vehicle Registration Certificate",docname=row.get('vehicle_no'))

def send_whatsapp_msg_to_process():
	need_to_process_list=frappe.get_all("Vehicle Tracking Log",{"docstatus":0,"status":['in',['Breakdown']],'driver_alert':['in',None]},['name','vehicle_no'])
	if need_to_process_list:
		for row in need_to_process_list:
			driver_details=frappe.db.get_value("User",{'driving_vehicle_no':row.get('vehicle_no'),"enabled":1},['email','mobile_no','username','full_name'],as_dict=True)
			if driver_details and driver_details.get('mobile_no'):
				if driver_details.get('mobile_no').startswith("+91"):
							receiver_whatsapp_no = driver_details.get('mobile_no')
							receiver_whatsapp_no.replace(" ","")
				else:
					receiver_whatsapp_no = "+91"+driver_details.get('mobile_no')
					receiver_whatsapp_no.replace(" ","")
				msg = f"Dear {driver_details.get('full_name')},\n\nGreeting from Liquiconnect Team!\n\nPlease update your vehicle's ({row.get('vehicle_no')}) previous log.\n\n"
				msg+=f"{frappe.utils.get_url()}/vehicle-tracking-log?name={quote(row.get('name'))}&&status={quote('Work in Progress')}"
				msg+="\n\nThanks,\nLiquiconnect Team."
				WhatsAppMessage.send_whatsapp_message(receiver_list=[receiver_whatsapp_no],message=msg,doctype="Vehicle Tracking Log",docname=row.get('name'))
				frappe.db.set_value("Vehicle Tracking Log", row.get('name'), "driver_alert", "Work in Progress")

def send_whatsapp_msg_to_complete():
	need_to_process_list=frappe.get_all("Vehicle Tracking Log",{"docstatus":0,"status":['in',['Work in Progress']],'driver_alert':['in',['Work in Progress']]},['name','vehicle_no','issue_based_on'])
	if need_to_process_list:
		for row in need_to_process_list:
			driver_details=frappe.db.get_value("User",{'driving_vehicle_no':row.get('vehicle_no'),"enabled":1},['email','mobile_no','username','full_name'],as_dict=True)
			if driver_details and driver_details.get('mobile_no'):
				if driver_details.get('mobile_no').startswith("+91"):
					receiver_whatsapp_no = driver_details.get('mobile_no')
					receiver_whatsapp_no.replace(" ","")
				else:
					receiver_whatsapp_no = "+91"+driver_details.get('mobile_no')
					receiver_whatsapp_no.replace(" ","")
				screen=None
				if row.get("issue_based_on") == "Breakdown":
					screen="breakdown"
				if row.get("issue_based_on") == "Preventive Maintenance":
					screen="preventive"
				if screen:
					msg = f"Dear {driver_details.get('full_name')},\n\nGreeting from Liquiconnect Team!\n\nPlease update your vehicle's ({row.get('vehicle_no')}) service report.\n\n"
					msg+=f"https://lnder-dev-client.el.r.appspot.com/#/submitreport/{screen}/{row.get('vehicle_no')}"
					msg+="\n\nThanks,\nLiquiconnect Team."
					WhatsAppMessage.send_whatsapp_message(receiver_list=[receiver_whatsapp_no],message=msg,doctype="Vehicle Tracking Log",docname=row.get('name'))
					frappe.db.set_value("Vehicle Tracking Log", row.get('name'), "driver_alert", "Complete")
