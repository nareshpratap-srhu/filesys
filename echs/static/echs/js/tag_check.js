 $(document).ready(function() {
        // Initialize Select2 for the custom tag dropdown
        $('#custom-tag-select').select2({
            placeholder: "-- Select a Tag --",
            allowClear: true
        });

        // Update the hidden input when a tag is selected
        // $('#custom-tag-select').on('change', function() {
        //     var selectedTag = $(this).val();
        //     $('#custom-tag-input').val(selectedTag);  // Set the hidden field with selected tag id
        // });

        $('#custom-tag-select').on('change', function () {

            let selectedTag = $(this).val();
            let uhid = $(this).data('uhid');           // Get UHID from data attribute
            let checkUrl = $(this).data('check-url');

            $('#custom-tag-input').val(selectedTag);

            if (!selectedTag) return;

            $.ajax({
                url: checkUrl,
                type: "GET",
                data: {
                    tag_id: selectedTag,
                    uhid: uhid
                },
                success: function (response) {
                    if (!response.allowed) {
                        window.location.href = response.redirect_url;
                    }
                },
                error: function () {
                    console.error("Discharge check failed");
                }
            });
        });
    });