-- Redirect includegraphics PDF paths to pre-converted PNGs in word_export/figures/
function Image(img)
  local name = img.src:match("([^/]+)%.pdf$")
  if name then
    img.src = "word_export/figures/" .. name .. ".png"
  end
  return img
end
