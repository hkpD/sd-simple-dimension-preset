onUiLoaded(function () {
  const row = gradioApp().querySelector("#txt2img_dimensions_row .form");
  const switchBtn = row.querySelector("#txt2img_res_switch_btn");

  const kacang = switchBtn.cloneNode(true);
  kacang.id = "kacang";
  kacang.title = "kacang kacang";
  kacang.innerText = "🥝";

  if (row && switchBtn) {
    row.insertBefore(kacang, switchBtn);
  }
});
