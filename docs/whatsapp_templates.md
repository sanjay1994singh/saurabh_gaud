# WhatsApp Templates

## 1. membership_account_created

Category: Utility

Language: Hindi

Header: None

Body:

```text
नमस्ते {{1}},

धर्म रक्षा संघ में आपका सदस्यता अकाउंट सफलतापूर्वक बन गया है।

यूजरनेम: {{2}}
पासवर्ड: {{3}}

सुरक्षा के लिए पहले लॉगिन के बाद पासवर्ड बदल लें।
```

Footer:

```text
धर्म रक्षा संघ
```

Variables:

```text
{{1}} सदस्य का पूरा नाम
{{2}} यूजरनेम, यही मोबाइल नंबर रहेगा
{{3}} अकाउंट बनाते समय बना प्रारंभिक पासवर्ड
```

## 2. certificate_download

Category: Utility

Language: Hindi

Header: Document

Document type: PDF

Body:

```text
नमस्ते {{1}},

धर्म रक्षा संघ में आपका सदस्यता अकाउंट सफलतापूर्वक बन गया है, और आपको सर्टिफिकेट भी प्राप्त हो गया है.
```

Footer:

```text
धर्म रक्षा संघ
```

Variables:

```text
{{1}} सदस्य का पूरा नाम
```

Backend Environment:

```env
WHATSAPP_API_URL=https://www.fast2sms.com/dev/whatsapp-session
WHATSAPP_DLT_MANAGER_URL=https://www.fast2sms.com/dev/dlt_manager/whatsapp
WHATSAPP_API_KEY=your-whatsapp-api-key
WHATSAPP_PHONE_NUMBER_ID=1228464747027462
WHATSAPP_API_VERSION=v26.0
WHATSAPP_TEMPLATE_ACCOUNT_CREATED=membership_account_created
WHATSAPP_TEMPLATE_CERTIFICATE_GENERATED=certificate_download
WHATSAPP_TEMPLATE_CERTIFICATE_MESSAGE_ID=30170
WHATSAPP_LANGUAGE_CODE=hi
```

Note:

```text
Account बनते ही membership_account_created template से username/password भेजे जाते हैं।
Certificate बनते ही certificate_download template के Document header में certificate PDF भेजा जाता है।
Paid membership में धर्म रक्षा संघ के नाम से invoice PDF अलग document message में भेजा जाता है।
```
