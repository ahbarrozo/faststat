// New objects to attempt using vue.js with jinja2 
// in the future
const myVue = Vue.extend({
  delimiters: ["@@", "@@"],
});


// Allow customized buttons to handle file input
function HandleBrowseClick()
{
  var fileinput = document.getElementById("filename");
  fileinput.click();
}
