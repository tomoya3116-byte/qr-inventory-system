(() => {
  const forms = document.querySelectorAll("form");

  forms.forEach((form) => {
    form.addEventListener("submit", (event) => {
      const button = event.submitter || form.querySelector("button[type='submit']");
      if (!button) {
        return;
      }
      button.dataset.originalText = button.textContent;
      button.textContent = "処理中...";
      button.disabled = true;
    });
  });
})();
