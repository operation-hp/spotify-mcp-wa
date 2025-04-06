## use google app script for handling spotify redirect URL 


function doGet(e) {
  const sheet = SpreadsheetApp.openById('10n6ckxCsmxfUPCHIKJNahitDGwUqRl8bXHxgbpSx4rY').getSheetByName('login');

  if (e.parameter.id) {
    // Step 2: Lookup by random number
    const targetId = e.parameter.id;
    const data = sheet.getDataRange().getValues();

   for (let i = 1; i < data.length; i++) {
      if (data[i][2].toString() === targetId) {
        const code = data[i][1];
        // Delete the row after reading it
        sheet.getRange(i + 1, 2).setValue('xxxx');
        return ContentService.createTextOutput(code);
      }
    }

    //return HtmlService.createHtmlOutput(`<p>No user found with ID ${targetId}</p>`);

  } else if (e.parameter.code) {
    // Step 1: Save data and generate random number
    const code = e.parameter.code;
    const randomId = Math.floor(Math.random() * 100000) + 1;
    sheet.appendRow([new Date(), code, randomId]);

    const baseUrl = ScriptApp.getService().getUrl();
    const link = `${baseUrl}?id=${randomId}`;

    return HtmlService.createHtmlOutput(
      `<h2>You login to Spotify and next step is to grant WhatsApp-MCPClient rights to search and play music.</h2>
       <p> Enter this unique ID <strong>${randomId}</strong> in the WhatsApp, only the numbers </p>
       <p><a href="${link}">The login session will be removed every 24 hrs. </a></p>`
    );
  } else {
    return HtmlService.createHtmlOutput(
      `<p>Please provide a query string like <code>?name=Peter</code> or <code>?id=12345</code></p>`
    );
  }
}
