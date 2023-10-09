# Copyright (c) 2023, Aerele and contributors
# For license information, please see license.txt

from hashlib import new
import frappe
import json
from frappe.model.document import Document
from datetime import datetime
from pymongo import MongoClient

class SmartTyreRealtimeData(Document):
	
	def db_insert(self):
		# Define the MongoDB connection string

		#@127.0.0.1:27017" -> Default database connection
		mongo_uri = "mongodb://root:root@172-31-35-242/admin"
		client = MongoClient(mongo_uri)
		db = client.get_database()

		# Insert a document into a MongoDB collection
		my_collection = db["my_collection"]
		data_to_insert = self.get_valid_dict(convert_dates_to_str=True)
		my_collection.insert_one(data_to_insert)

		# Close the MongoDB client when done
		client.close()

	def load_from_db(self):
		pass

	def db_update(self):
		pass

	def get_list(self, args):
		pass

	def get_count(self, args):
		pass

	def get_stats(self, args):
		pass

def get_smart_tyre_data(
		vehicle_no=None,
		device_id=None,
		from_date=None,
		to_date=None,
		limit=None,
		sort=None
	):
	
	# from_date = str(datetime(2023, 10, 6, 00, 00, 00, 00))
	# to_date = str(datetime(2023, 10, 10, 23, 59, 59, 00))

	#filters
	filters ={}
	if from_date and to_date:
		filters["modified"]={
							"$gte": from_date,
							"$lte": to_date
							}
	if vehicle_no:
		filters["vehicle_no"]=vehicle_no
	if device_id:
		filters["device_id"]=device_id
	
	limit = int(limit) if limit and int(limit) else 0
	sort = 1 if sort=="ASC" else -1
	
	#Create MongoDB connection
	mongo_uri = "mongodb://root:root@172-31-35-242/admin"
	client_server = MongoClient(mongo_uri)
	client_server_db = client_server.get_database()
	client_server_collection = client_server_db["my_collection"]

	# Perform a query to fetch data
	results = client_server_collection.find(filters).sort([("modified", sort)]).limit(limit)
	
	
	data=[]
	for result in results:
		data.append(result)
	#close client
	client_server.close()

	return data