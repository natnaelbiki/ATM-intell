document.addEventListener('DOMContentLoaded', function () {
    const uploadButton = document.getElementById('upload-button');
    const excel_file = document.getElementById('excel_file');
    const progressBar = document.getElementById('upload-progress');

    uploadButton.addEventListener('click', function () {
        const file = excel_file.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);  // Match the key with your Django view's expected key

            const xhr = new XMLHttpRequest();
            xhr.open('GET', '/financial_reports/', true);  // Replace '/your-upload-url/' with your actual upload URL
            xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));  // Django CSRF token header

            // Update progress bar during the upload
            xhr.upload.onprogress = function (event) {
                if (event.lengthComputable) {
                    const percentage = (event.loaded / event.total) * 100;
                    progressBar.value = percentage;
                }
            };

            // Handle the response from the server
            xhr.onload = function () {
                if (xhr.status == 200) {
                    alert('Upload complete!');
                    progressBar.value = 0;  // Reset the progress bar
                } else {
                    alert('Upload failed!');
                    progressBar.value = 0;  // Reset the progress bar
                }
            };

            xhr.send(formData);
        }
    });
});

// Function to get Django CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
