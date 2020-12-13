from django import forms

class newUserRegistration(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'type': 'text', 'id':'register-form-name', 'name':'register-form-name','for':'username', 'class':'input-text'}))
    ps = forms.CharField(widget=forms.TextInput(attrs={'type': 'password', 'id':'register-form-name', 'name':'register-form-name','for':'username', 'class':'input-text'}))
    Target = forms.CharField(widget=forms.TextInput(attrs={'type': 'text', 'id':'register-form-name', 'name':'register-form-name','for':'username', 'class':'input-text'}))
    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']
        
        return data