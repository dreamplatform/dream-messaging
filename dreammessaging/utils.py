
class AjaxSnippetTemplateResponseMixin(object):
  def get_template_names(self):
    templates = super(AjaxSnippetTemplateResponseMixin, self).get_template_names()
    if self.request.is_ajax() or 'popup' in self.request.GET:
      for i, template in enumerate(templates):
        templates[i] = template.replace('.html', '.popup.html')
    return templates

