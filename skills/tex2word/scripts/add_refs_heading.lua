-- Insert an unnumbered "References" heading before the citeproc bibliography div.
-- Must be passed AFTER --citeproc on the pandoc command line.
function Pandoc(doc)
  for i, b in ipairs(doc.blocks) do
    if b.t == "Div" and b.identifier == "refs" then
      table.insert(doc.blocks, i,
        pandoc.Header(1, "References", pandoc.Attr("", {"unnumbered"})))
      break
    end
  end
  return doc
end
