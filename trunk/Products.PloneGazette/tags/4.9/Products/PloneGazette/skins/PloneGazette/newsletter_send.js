(function($) {
NewsletterSend = function(context){
    var self = this;
    var base = $("base").attr('href') || document.baseURI || window.location.href.split("?")[0];

    self.url = base + "/getSendStatus";
    self.context = context.get(0);
    self.submit_btn = $("input[type='submit']", context).get(0);

    $(context).submit(function(){
        $(self.submit_btn).val("Please wait while sending newsletter");
        self.submit_btn.disabled = true;
        var submit_url = $(self.context).attr("action");

        jQuery.ajax({
            url:submit_url,
            'type':'POST',
            'data':'submit=submit',
            cache:false,
            success:function(xhr){
                $(self.context).html("Newsletter sent succesfully");
            },
            error:function(xhr){
                $(self.context).html("There was an error sending the newsletter. " + 
                    "This might be due to server timeout, so check that no " + 
                    "newsletter has been sent before trying again.");
            }
        });
        setTimeout(function(){ 
            self.check_sent_status.call(self);
        }, 2000);
        return false;
    });
};

NewsletterSend.prototype.check_sent_status = function(){
    var self = this;
    jQuery.ajax({
        url:self.url, 
        cache:false,
        success: function(text) {
            if (text != "OK") {
                setTimeout(function(){
                    self.check_sent_status.call(self);
                }, 2000);
                return false;
            } else {
                $(self.submit_btn).val("Done.");
            }
        },
        error:function(xhr) {
            setTimeout( function(){
                self.check_sent_status.call(self);
            }, 2000);
            this.submit_btn.val("Still trying.");
            return false;
        }
    });
}
})(jQuery);