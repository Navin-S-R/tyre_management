// Copyright (c) 2023, Aerele and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tyre Maintenance', {
	"vehicle_no": function(frm){
		if (frm.doc.vehicle_no && frm.doc.ref_doctype){
			frappe.call({
				"method": "tyre_management.tyre_management.doctype.tyre_maintenance.tyre_maintenance.get_latest_tyre_position_for_vehicle",
				"args":{
					"doctype" : frm.doc.ref_doctype,
					"vehicle_no" : frm.doc.vehicle_no
				},
				callback: function(r){
					if(r.message){
						frm.set_value("vehicle_tire_position",r.message);
					}
				}
			})
		}
	}
});
