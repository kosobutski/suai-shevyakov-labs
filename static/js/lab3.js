function getClimateData() {
  $.ajax({
    type: "GET",
    url: "/connect/climate",
    dataType: "json",
    contentType: "application/json",
    data: {},
    success: function (response) {
      $("#climate_device").val(response.device);
      $("#climate_zone").val(response.zone);
      $("#climate_temperature").val(response.temperature_c);
      $("#climate_humidity").val(response.humidity_percent);
    }
  });
}

function getSoilData() {
  $.ajax({
    type: "GET",
    url: "/connect/soil",
    dataType: "json",
    contentType: "application/json",
    data: {},
    success: function (response) {
      $("#soil_device").val(response.device);
      $("#soil_zone").val(response.zone);
      $("#soil_moisture").val(response.moisture_percent);
    }
  });
}

function getValveData() {
  $.ajax({
    type: "GET",
    url: "/connect/valve",
    dataType: "json",
    contentType: "application/json",
    data: {},
    success: function (response) {
      $("#valve_device").val(response.device);
      $("#valve_zone").val(response.zone);
      $("#valve_state").val(response.is_open ? "Открыт" : "Закрыт");
      $("#valve_flow").val(response.flow_l_per_min);
    }
  });
}

function updateAll() {
  getClimateData();
  getSoilData();
  getValveData();
}

$(function () {
  updateAll();
  setInterval(updateAll, 1000);
});
