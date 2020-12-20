from django import forms
choice =( 
    ("amazon", "Amazon"),
    ("ebay", "Ebay"), 
) 
class newUserRegistration(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'type': 'text', 'id':'username', 'name':'register-form-name','for':'username', 'class':'input-text'}))
    ps = forms.CharField(widget=forms.TextInput(attrs={'type': 'password', 'id':'ps', 'name':'register-form-name','for':'username', 'class':'input-text'}))
    Target = forms.CharField(widget=forms.TextInput(attrs={'type': 'text', 'id':'target', 'name':'register-form-name','for':'username', 'class':'input-text'}))
    geeks_field = forms.ChoiceField(choices = choice)
    maxP = forms.IntegerField()
    minP = forms.IntegerField()
    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']
        
        return data