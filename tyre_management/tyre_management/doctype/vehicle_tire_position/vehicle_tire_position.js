// Copyright (c) 2023, Aerele and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vehicle Tire Position', {
	refresh: function(frm) {
		frm.set_query("ref_doctype", function(frm) {
			return { filters: {"name":['in',["Vehicle","Vehicle Registration Certificate"]]}};
		});
	},
	customer: function(frm) {
		if (cur_frm.doc.customer){
			let serial_no_fields = [
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
				"rear_right_4",
				"spare_1",
				"spare_2"
			]
			serial_no_fields.forEach((element)=>{
				frm.set_query(element, function(frm) {
					return { filters: {"customer": cur_frm.doc.customer}};
				});
			})
		}
	}
});
