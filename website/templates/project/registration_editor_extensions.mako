<!-- OSF Upload -->
<script type="text/html" id="osf-upload">
  <a data-bind="click: toggleUploader">Attach File</a>
  <span data-bind="visible: showUploader">
    <div id="selectedFile">File selected for upload:  
      <span id="fileName" data-bind="text: selectedFileName">no file selected</span>
    </div>
    <div data-bind="attr.id: $data.id, osfUploader"></div>
  </span>
</script>
