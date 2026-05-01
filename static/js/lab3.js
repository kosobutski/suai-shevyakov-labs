// ========== Мониторинг (ЛР3) ==========
function getClimateData() {
  $.ajax({
    type: "GET",
    url: "/connect/climate",
    dataType: "json",
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
    success: function (response) {
      $("#valve_device").val(response.device);
      $("#valve_zone").val(response.zone);
      $("#valve_state").val(response.is_open ? "Открыт" : "Закрыт");
      $("#valve_flow").val(response.flow_l_per_min);
      $("#valve_auto_mode").val(response.auto_mode ? "Включён" : "Выключен");
      $("#valve_threshold").val(response.moisture_threshold);
      $("#auto_mode_btn").text(response.auto_mode ? "Выключить" : "Включить");
      $("#threshold_set").val(response.moisture_threshold);
    }
  });
}

function updateAll() {
  getClimateData();
  getSoilData();
  getValveData();
}

// ========== Ручные команды (ЛР4, ЛР5) ==========
function sendClimateCommand() {
  let temp = $("#climate_temp_set").val();
  let hum = $("#climate_hum_set").val();
  let params = {};
  if (temp !== "") params.temperature_c = temp;
  if (hum !== "") params.humidity_percent = hum;
  if (Object.keys(params).length === 0) {
    $("#climate_result").text("Ошибка: введите параметры").css("color", "red");
    return;
  }
  $.ajax({
    type: "GET",
    url: "/control/climate",
    data: params,
    dataType: "json",
    success: function (resp) {
      $("#climate_result").text("✓ " + resp.result).css("color", "green");
      updateAll();
    },
    error: function () {
      $("#climate_result").text("Ошибка соединения").css("color", "red");
    }
  });
}

function sendSoilCommand() {
  let moisture = $("#soil_moist_set").val();
  if (moisture === "") {
    $("#soil_result").text("Ошибка: введите влажность").css("color", "red");
    return;
  }
  $.ajax({
    type: "GET",
    url: "/control/soil",
    data: { moisture_percent: moisture },
    dataType: "json",
    success: function (resp) {
      $("#soil_result").text("✓ " + resp.result).css("color", "green");
      updateAll();
    }
  });
}

function sendValveCommand(open) {
  $.ajax({
    type: "GET",
    url: "/control/valve",
    data: { open: open },
    dataType: "json",
    success: function (resp) {
      $("#valve_result").text("✓ " + resp.result).css("color", "green");
      updateAll();
    }
  });
}

function sendValveFlowCommand() {
  let flow = $("#valve_flow_set").val();
  if (flow === "") {
    $("#valve_result").text("Ошибка: введите расход").css("color", "red");
    return;
  }
  $.ajax({
    type: "GET",
    url: "/control/valve",
    data: { flow_l_per_min: flow },
    dataType: "json",
    success: function (resp) {
      $("#valve_result").text("✓ " + resp.result).css("color", "green");
      updateAll();
    }
  });
}

// ========== Автоматический режим (ЛР6) ==========
function toggleAutoMode() {
  let currentAuto = $("#valve_auto_mode").val() === "Включён";
  let newMode = !currentAuto;
  $.ajax({
    type: "GET",
    url: "/control/valve",
    data: { auto_mode: newMode },
    dataType: "json",
    success: function (resp) {
      $("#auto_result").text("✓ " + resp.result).css("color", "green");
      updateAll();
    },
    error: function () {
      $("#auto_result").text("Ошибка").css("color", "red");
    }
  });
}

function setThreshold() {
  let threshold = $("#threshold_set").val();
  if (threshold === "") {
    $("#auto_result").text("Ошибка: введите порог").css("color", "red");
    return;
  }
  $.ajax({
    type: "GET",
    url: "/control/valve",
    data: { moisture_threshold: threshold },
    dataType: "json",
    success: function (resp) {
      $("#auto_result").text("✓ " + resp.result).css("color", "green");
      updateAll();
    }
  });
}

$(function () {
  updateAll();
  setInterval(updateAll, 1000);
});