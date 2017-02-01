function launchModal(src, title) {
  var image = document.getElementById('modal-image');
  image.setAttribute('src', src);
  image.setAttribute('title', title);
  var modal = document.getElementById('modal');
  var currentClass = modal.getAttribute('class');
  modal.setAttribute('class', currentClass + ' show');
}

function closeModal() {
  var modal = document.getElementById('modal');
  modal.className = 'tc-modal';
}

window.onload = function () {
  var images = document.getElementsByTagName("img")
  for (var i = 0; i < images.length; i++) {
    images[i].addEventListener("click", function(){
        launchModal(this.src, this.title);
    });
  };
  document.getElementById("modal").addEventListener("click", closeModal)
};
