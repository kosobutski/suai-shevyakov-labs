// ========== Функции мониторинга (из ЛР3, не изменены) ==========
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


function sendClimateCommand() {
  let temp = $("#climate_temp_set").val();
  let hum = $("#climate_hum_set").val();
  let params = {};
  if (temp !== "") params.temperature_c = temp;
  if (hum !== "") params.humidity_percent = hum;
  if (Object.keys(params).length === 0) {
    $("#climate_result").text("Ошибка: введите хотя бы один параметр").css("color", "red");
    return;
  }
  $.ajax({
    type: "GET",
    url: "/control/climate",
    data: params,
    dataType: "json",
    success: function (resp) {
      if (resp.status === "ok") {
        $("#climate_result").text("✓ " + resp.result).css("color", "green");
        updateAll();  // обновляем мониторинг
      } else {
        $("#climate_result").text("Ошибка: " + JSON.stringify(resp)).css("color", "red");
      }
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
      if (resp.status === "ok") {
        $("#soil_result").text("✓ " + resp.result).css("color", "green");
        updateAll();
      } else {
        $("#soil_result").text("Ошибка: " + JSON.stringify(resp)).css("color", "red");
      }
    },
    error: function () {
      $("#soil_result").text("Ошибка соединения").css("color", "red");
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
      if (resp.status === "ok") {
        $("#valve_result").text("✓ " + resp.result).css("color", "green");
        updateAll();
      } else {
        $("#valve_result").text("Ошибка: " + JSON.stringify(resp)).css("color", "red");
      }
    },
    error: function () {
      $("#valve_result").text("Ошибка соединения").css("color", "red");
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
      if (resp.status === "ok") {
        $("#valve_result").text("✓ " + resp.result).css("color", "green");
        updateAll();
      } else {
        $("#valve_result").text("Ошибка: " + JSON.stringify(resp)).css("color", "red");
      }
    },
    error: function () {
      $("#valve_result").text("Ошибка соединения").css("color", "red");
    }
  });
}

// Запуск автоматического обновления мониторинга (как в ЛР3)
$(function () {
  updateAll();
  setInterval(updateAll, 1000);
});