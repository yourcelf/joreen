const xhr = {
  get: function(url, data) {
    return new Promise((resolve, reject) => {
      if (data) {
        let parts = [];
        for (var key in data) {
          parts.push(encodeURIComponent(key) + "=" + encodeURIComponent(data[key]));
        }
        url = url + "?" + parts.join('&');
      }
      console.log("GET", url);
      let xmlhttp = new XMLHttpRequest();
      xmlhttp.onreadystatechange = function(event) {
        console.log(xmlhttp.readyState, event);
        if (XMLHttpRequest.DONE !== xmlhttp.readyState) {
          return;
        }
        if (xmlhttp.status == 200) {
          return resolve(JSON.parse(xmlhttp.responseText));
        } else {
          return reject(xmlhttp.responseText);
        }
      }
      xmlhttp.open('GET', url, true);
      xmlhttp.send();
    });
  }
}

export default xhr;
