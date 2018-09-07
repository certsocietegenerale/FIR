function isNumber(n) {
  return !isNaN(parseFloat(n)) && isFinite(n);
}

var color = d3.scale.ordinal()
	    .range(["#e60028", "#873d67", "#3e7eaf", "#d55a39", "#1a9656", "#666666", "#d24b28", "#0ac8dc", "#82379b", "#a50041", "#a0af00", "#ffa02d", "#c30082", "#00a550", "#64a0c8", "#c864cd", "#dc4b69", "#9be173", "#ffb414", "#e1648c", "#9178d2", "#6e3c28"]);


var color_severity = d3.scale.ordinal()
					.domain(['1/4', '2/4', '3/4', '4/4'])
					.range(['#468847', '#f89406', '#fefe00', '#f81920']);

var colors = {other: color, severity: color_severity};

function generate_table(selector, url) {
	$.getJSON(url, function(data) {

		var table = $(selector);

		$.each(data, function(key, incident) {
			tr = $('<tr />');
			tr.append("<td>"+moment(incident.date, 'YYYY-MM-DD HH:mm').format('YYYY-MM-DD HH:mm')+"</td>");
			tr.append("<td>"+incident.id+"</td>");
			tr.append("<td>"+incident.subject+"</td>");
			tr.append("<td>"+incident.category+"</td>");
			tr.append("<td>"+incident.confidentiality_display+"</td>");
			tr.append("<td><span class='badge threatcon-"+incident.severity+"'>"+incident.severity+"</span></td>");
			tr.append("<td>"+incident.business_lines_names+"</td>");
			tr.append("<td>"+incident.status_display+"</td>");
			tr.append("<td>"+incident.detection+"</td>");
			tr.append("<td>"+incident.actor+"</td>");
			tr.append("<td>"+incident.last_comment_action+"</td>");
			tr.append("<td>"+incident.opened_by+"</td>");
			tr.append("<td>"+incident.plan+"</td>");
			table.append(tr);
		});
	});
}

function generate_variation_chart(selector, url) {
	$.getJSON(url, function(data) {
		  var rows = [];

		  var up = '<i class="icon-plus-sign"></i>';
		  var down = '<i class="icon-minus-sign"></i>';

		  var table = $(selector);
		  table.empty();


		  var cat = [];
		  var _new = [];
		  var _var = [];
		  var _icon = [];

		  $.each(data, function(key, val) {

		  	cat.push(val.category);
		  	_new.push(val.values.new);
		  	_var.push(val.values.variation);
			var icon;
		  	if (+val.values.variation > 0)
		  		icon = up;
		  	else if (+val.values.variation < 0)
		  		icon = down;
		  	else
		  		icon = "";

		  	_icon.push(icon);
		  });

		  var cat_row = $("<tr/>");
		  cat_row.append("<th></th>");
		  $.each(cat, function(key, val) {
		  	cat_row.append("<th>"+val+"</th>")
		  });
		  table.append(cat_row);

		  var _new_row = $("<tr/>");
		  _new_row.append("<th style='text-align:right'>New</th>");
		  $.each(_new, function(key, val) {
		  	_new_row.append("<td>"+val+"</td>")
		  });
		  table.append(_new_row);

		  var _var_row = $("<tr/>");
		  _var_row.append("<th style='text-align:right'>Variation</th>");
		  $.each(_var, function(key, val) {
		  	_var_row.append("<td>"+val+"</td>")
		  });
		  table.append(_var_row);

		  var _icon_row = $("<tr/>");
		  _icon_row.append("<th></th>");
		  $.each(_icon, function(key, val) {
		  	_icon_row.append("<td>"+val+"</td>")
		  });
		  table.append(_icon_row);
		});
}


function generate_stacked_chart(selector, url, width, height, label, legend) {

	var margin = {top: 20, right: 20, bottom: 30, left: 40},
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;

	d3.json(url, function(error, data) {

		var legend_per_col = (Math.floor(height/20));
		legend = Object.keys(data[0]).length-1;

		width = width + margin.left + margin.right - 120 * Math.floor(legend/legend_per_col);
		var color_scale = color;
		var svg = d3.select(selector).append("svg")
		    .attr("width", width)
		    .attr("height", height + margin.top + margin.bottom)
		  .append("g")
		    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

		  color.domain(d3.keys(data[0]).filter(function(key) { return key !== "entry"; }));

		  data.forEach(function(d) {
		    var y0 = 0;
			var type;
		    if (d['1/4'] != undefined) {
		    	type = 'severity';
		    	color_scale = color_severity
		    }
		   	else {
		   		type = 'other';
		   		color_scale = color
		   	}
		    d.values = color.domain().map(function(name) { 	return {name: name, y0: y0, y1: y0 += +d[name], type: type}; });
		    d.total = d.values[d.values.length - 1].y1;
	  });

		var x = d3.scale.ordinal()
		    .rangeRoundBands([0, width], .1);

		var y = d3.scale.linear()
		    .rangeRound([height, 0]);

		var xAxis = d3.svg.axis()
		    .scale(x)
		    .orient("bottom");

		var yAxis = d3.svg.axis()
		    .scale(y)
		    .orient("left")
		    .tickFormat(d3.format(".2s"));

	  x.domain(data.map(function(d) { return d.entry; }));
	  y.domain([0, d3.max(data, function(d) { return d.total; })]);

	  svg.append("g")
	      .attr("class", "x axis")
	      .attr("transform", "translate(0," + height + ")")
	      .call(xAxis);

	  svg.append("g")
	      .attr("class", "y axis")
	      .call(yAxis)
	    .append("text")
	      .attr("transform", "rotate(-90)")
	      .attr("y", 6)
	      .attr("dy", ".71em")
	      .style("text-anchor", "end")
	      .text(label);

	  var entry = svg.selectAll(".entry")
	      .data(data)
	    .enter().append("g")
	      .attr("class", "g")
	      .attr("transform", function(d) { return "translate(" + x(d.entry) + ",0)"; });

	  entry.selectAll("rect")
	      .data(function(d) { return d.values; })
	    .enter().append("rect")
	      .attr("width", x.rangeBand())
	      .attr("y", function(d) { return y(d.y1); })
	      .attr("height", function(d) { return y(d.y0) - y(d.y1); })
	      .attr('title', function(d) { return d.y1-d.y0})
	      .attr('data-toggle', 'tooltip')
	      .style("fill", function(d) {
	      	return colors[d.type](d.name)
	      });


	  var legend = svg.selectAll(".legend")
	      .data(color.domain().slice().reverse())
	    .enter().append("g")
	      .attr("class", "legend")
	      .attr("transform", function(d, i) {
	      	legend_per_col = (Math.floor(height/20));
	      	w = width+60+(Math.floor(i/legend_per_col)+1)*130;
	      	d3.select(selector).select('svg').style('width', w+'px');
	      	return "translate("+ Math.floor(i/legend_per_col) * 130 +"," + (i%legend_per_col) * 20 + ")";
	      });

	  legend.append("rect")
	      .attr("x", width + 20)
	      .attr("width", 18)
	      .attr("height", 18)
	      .style("fill", function(d) {
	      	return color_scale(d)
	      });


	  legend.append("text")
	      .attr("x", width + 53)
	      .attr("y", 9)
	      .attr("dy", ".35em")
	      //.style("text-anchor", "end")
	      .text(function(d) { return d; });

	});
}


function generate_bar_chart(selector, url, width, height, label) {

	var margin = {top: 20, right: 20, bottom: 30, left: 50},
	    width = width - margin.left - margin.right,
		height = height - margin.top - margin.bottom;

	var parseDate = d3.time.format("%b").parse;

	var x = d3.scale.ordinal()
    .rangeRoundBands([0, width], .1);

	var y = d3.scale.linear()
	    .rangeRound([height, 0]); // was .range()

	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom");

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left")
	    .tickFormat(d3.format(".2s")); //no tickformat

	var svg = d3.select(selector).append("svg")
	    .attr("width", width + margin.left + margin.right)
	    .attr("height", height + margin.top + margin.bottom)
	  .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.json(url, function(error, data) {
		 color.domain([]);
		data.forEach(function (d) {
			d.label = d.label
		});

		x.domain(data.map(function (d) { return d.label }));
		y.domain([0, d3.max(data, function(d) { return d.value })]);

		// axis x
		var lower_axis = svg.append("g")
			.attr("class", "x axis")
			.attr("transform", "translate(0, " + height + ")")
			.call(xAxis)
			.selectAll('text');

		// axis y
		svg.append("g")
			.attr("class", "y axis")
			.call(yAxis)
			.append("text")
			.attr("transform", "rotate(-90)")
			.attr("y", 6)
			.attr("dy", ".71em")
			.style("text-anchor", "end")
			.text(label);

		var bars = svg.selectAll('g.bar').data(data).enter().append("g").attr('class','bar');

		var column_width = 0;

		bars.append('rect')
			.attr('class', 'bar')
			.attr('x', function (d) { return x(d.label); })
			.attr('width', function(d) { column_width = x.rangeBand(); return x.rangeBand()} )
			.attr('y', function (d) { return y(d.value); })
			.attr("height", function(d) { return height - y(d.value); })
			.style("fill", function(d) { return color(d.label); });

		var max_len_label = d3.max(data, function(d) { return d.label.length });

		if (max_len_label*7>column_width) {
			lower_axis.attr("transform", "rotate(-90)")
				.style('text-anchor', 'end')
				.attr("dy", -8)
				.attr('dx', -10);

			var frame = d3.select(selector).select("svg");

			frame.attr('height', +frame.attr('height') + (max_len_label*6.5))

			}


		bars.append('text')
			.attr('x', function(d) {
				return x(d.label)+x.rangeBand()/2 })
			.attr('y', function(d) {
				return y(d.value) })
			.text(function(d) {
				if (d.text == d.value)
					return "";
				return d.text
			})

			.attr("dy", function(d){
				if (y(d.value) > height-20)
					return -20;
				else
					return 20
			}) // padding-right
			.attr('text-anchor', 'middle');

		bars.append('text')
			.attr('x', function(d) {
				return x(d.label)+x.rangeBand()/2 })
			.attr('y', function(d) {
				return y(d.value) })
			.text(function(d) {
				return d.value })
			.attr("dy", -3) // padding-right
			.attr('text-anchor', 'middle')

	});
}

function generate_multiple_donut_chart(selector, url, widths, outer_radius, inner_radius) {

	var padding = 10;

	var arc = d3.svg.arc()
	    .outerRadius(outer_radius)
	    .innerRadius(inner_radius);

	var pie = d3.layout.pie()
	    .sort(null)
	    .value(function(d) { return d.value; });

	d3.json(url, function(error, data) {
	  color.domain(d3.keys(data[0]).filter(function(key) { return key !== 'entry'; }));

	  data.forEach(function(d) {
	  	total = 0;
	  	for (var index in d) {
	  		if (isNumber(d[index]))
	  			total += d[index];
	  	}
	  	if (d['1/4'] != undefined) {
		    	type = 'severity';
		    	color_scale = color_severity
	    }
	   	else {
	   		type = 'other';
	   		color_scale = color
	   	}
	   	if (total == 0)
	    		na = true;
	    	else
	    		na = false;
	    d.entries = color.domain().map(function(name) {
	    	if (na) {	return {name: "N/A", value: 1, type: 'other', na: na }}
	    	else {   	return {name: name, value: +d[name], type: type, na: na}; }
	    });
	  });

	  var svg = d3.select(selector).selectAll(".pie")
	      .data(data)
	    .enter().append("svg")
	      .attr("class", "pie")
	      .attr("width", outer_radius * 2)
	      .attr("height", outer_radius * 2)
	    .append("g")
	      .attr("transform", "translate(" + outer_radius + "," + outer_radius + ")");

	var g = svg.selectAll(".arc")
	      .data(function(d) { return pie(d.entries); })
	    .enter().append("g");

	  g.append('path')
	      .attr("class", "arc")
	      .attr("d", arc)
	      .style("fill", function(d) {
	      	if (d.data.na) {
	      		return "#CCC";
	      	}
	      	return colors[d.data.type](d.data.name);
	      });

	  g.append("text")
	      .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
	      .attr("dy", ".35em")
	      .style("text-anchor", "middle")
	      .text(function(d) {
	      	if (d.data.na)
	      		return "N/A";
	      	if (d.data.value != 0)
	      		return d.data.value;
	      });

	  svg.append("text")
	      .attr("dy", ".35em")
	      .style("text-anchor", "middle")
	      .text(function(d) { return d.entry; });

	  $(selector).width(widths)

	});

}


function generate_donut_chart(selector, url, dimension, radius) {
  var width = dimension,
      height = dimension,
      radius = radius;

  var arc = d3.svg.arc()
      .outerRadius(radius - 10)
      .innerRadius((radius - 10)/2);

  var pie = d3.layout.pie()
      .sort(null)
      .value(function(d) { return d.value; });

  var svg = d3.select(selector).append("svg")
      .attr("width", width)
      .attr("height", height)
    .append("g")
      .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

  d3.json(url, function(error, data) {
	  var color_scale;
      if (data[0].label == "1/4") {
		  color_scale = color_severity;
	  } else {
		  color_scale = color;
      }

      color.domain([]);

      data.forEach(function(d) {
        d.count = +d.count;
      });

      var g = svg.selectAll(".arc")
          .data(pie(data))
        .enter().append("g")
          .attr("class", "arc");

      g.append("path")
          .attr("d", arc)
          .style("fill", function(d) { return color_scale(d.data.label); });

      g.append("text")
          .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
          .attr("dy", ".35em")
          .style("text-anchor", "middle")
          .text(function(d) {
          	return d.data.value;
          });

          var legend_height = Math.max(data.length*20, dimension);

    	  var legend = d3.select(selector).append("svg")
          .attr("class", "legend")
          .attr("width", radius)
          .attr("height", legend_height)
        	.selectAll("g")
          	.data(color_scale.domain().slice().reverse())
        	.enter().append("g")
         	.attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

      legend.append("rect")
          .attr("width", 18)
          .attr("height", 18)
          .style("fill", color_scale);

      legend.append("text")
          .attr("x", 24)
          .attr("y", 9)
          .attr("dy", ".35em")
          .text(function(d) { return d; });

  });

}

function generate_multiple_line_chart(selector, url, width, height, dateformat, ylabel) {
	var margin = {top: 20, right: 80, bottom: 30, left: 50},
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;

	var parseDate = d3.time.format(dateformat).parse;

	var x = d3.time.scale()
	    .range([0, width]);

	var y = d3.scale.linear()
	    .range([height, 0]);

	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom")
	    .tickFormat(d3.time.format("%Y/%m"));

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left");

	var line = d3.svg.line()
	    .interpolate("basis")
	    .x(function(d) { return x(d.date); })
	    .y(function(d) { return y(d.value); });

	var svg = d3.select(selector).append("svg")
	    .attr("width", width + margin.left + margin.right)
	    .attr("height", height + margin.top + margin.bottom)
	  .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.json(url, function(error, data) {
	  color.domain(d3.keys(data[0]).filter(function(key) { return key !== "date"; }));

	  data.forEach(function(d) {
	    d.date = parseDate(d.date);
	  });

	  var values = color.domain().map(function(name) {
	    return {
	      name: name,
	      values: data.map(function(d) {
	        return {date: d.date, value: +d[name]};
	      })
	    };
	  });

	  x.domain(d3.extent(data, function(d) { return d.date; }));

	  y.domain([
	    0,
	    d3.max(values, function(c) { return d3.max(c.values, function(v) { return v.value; }); })
	  ]);



	  svg.append("g")
	      .attr("class", "x axis")
	      .attr("transform", "translate(0," + height + ")")
	      .call(xAxis);

	  svg.append("g")
	      .attr("class", "y axis")
	      .call(yAxis)
	    .append("text")
	      .attr("transform", "rotate(-90)")
	      .attr("y", 6)
	      .attr("dy", ".71em")
	      .style("text-anchor", "end")
	      .text(ylabel);

	  var item = svg.selectAll(".item")
	      .data(values)
	    .enter().append("g")
	      .attr("class", "item");

	  item.append("path")
	      .attr("class", "line")
	      .attr("d", function(d) {
	      	return line(d.values);
	      })
	      .style("stroke", function(d) {
	      	return color(d.name);
	      });

	  item.append("text")
	      .datum(function(d) { return {name: d.name, value: d.values[0]}; })
	      .attr("transform", function(d) { return "translate(" + x(d.value.date) + "," + y(d.value.value) + ")"; })
	      .attr("x", 3)
	      .attr("dy", ".35em")
	      .text(function(d) { return d.name; });
	});


}

function generate_line_chart(selector, url, width, height) {

	var margin = {top: 20, right: 20, bottom: 30, left: 50},
    width = width - margin.left - margin.right,
	    height = height - margin.top - margin.bottom;

	var parseDate = d3.time.format("%Y-%m").parse;

	var x = d3.time.scale()
	    .range([0, width]);

	var y = d3.scale.linear()
	    .range([height, 0]);

	var xAxis = d3.svg.axis()
	    .scale(x)
	    .orient("bottom");

	var yAxis = d3.svg.axis()
	    .scale(y)
	    .orient("left");

	var line = d3.svg.line()
	    .interpolate("basis")
	    .x(function(d) { return x(d.label); })
	    .y(function(d) { return y(d.value); });

	var svg = d3.select(selector).append("svg")
	    .attr("width", width + margin.left + margin.right)
	    .attr("height", height + margin.top + margin.bottom)
	  .append("g")
	    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	d3.json(url, function(error, chart_data) {

		chart_data.forEach(function (data){

			data.forEach(function (d) {
			  	d.label = parseDate(d.label)
			  });

				x.domain(d3.extent(data, function(d) { return d.label; }));
				y.domain(d3.extent(data, function(d) {  return d.value; }));

			  svg.append("g")
			      .attr("class", "x axis")
			      .attr("transform", "translate(0," + height + ")")
			      .call(xAxis);

			  svg.append("g")
			      .attr("class", "y axis")
			      .call(yAxis)
			    .append("text")
			      .attr("transform", "rotate(-90)")
			      .attr("y", 6)
			      .attr("dy", ".71em")
			      .style("text-anchor", "end");

			  svg.append("path")
			      .datum(data)
			      .attr("class", "line")
			      .attr("d", line);
			});

		});
}
