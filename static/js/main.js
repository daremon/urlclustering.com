function hasMinChars(obj, min_chars) {
  if (obj.val().length< min_chars) {
    showError(obj);
    return false;
  }
  hideError(obj);
  return true;
}

function showError(obj) {
  obj.css('border-color', '#aa0000');
  obj.focus();
}

function hideError(obj) {
  obj.css('border-color', '#000000');
}

function cluster(url) {
  var res = {};
  $('#results').html('<img src="/static/images/loader.gif">');
  $('#go').prop('disabled', true)
  $.ajax({
    type: 'GET',
    url: '/action/cluster',
    data: 'url=' + escape(url),
    dataType: "json",
  }).done(function(data) {
    console.log(data);
    if (data.error != undefined)
      $('#results').html(data.error);
    else
      $('#results').html(data.html);
    $('#go').prop('disabled', false)
  });
}

function go() {
  if (!hasMinChars($('#url'), 4)) return false;
  cluster($('#url').val());
}
