-- clean_toc.lua
-- Remove embedded DOCX TOC blocks so output uses generated TOC.

local utils = pandoc.utils

local function lower(value)
  if not value then
    return ""
  end
  return tostring(value):lower()
end

local function has_toc_marker(attr)
  if not attr then
    return false
  end

  for _, class_name in ipairs(attr.classes or {}) do
    if lower(class_name):find("toc", 1, true) then
      return true
    end
  end

  for key, value in pairs(attr.attributes or {}) do
    if lower(key):find("toc", 1, true) then
      return true
    end
    if lower(value):find("toc", 1, true) then
      return true
    end
  end

  return false
end

local function is_toc_heading(header)
  local text = lower(utils.stringify(header.content))
  return text == "contents" or text == "toc" or text == "table of contents"
end

function Div(div)
  if has_toc_marker(div.attr) then
    return {}
  end
  return nil
end

function Header(header)
  if is_toc_heading(header) then
    header.classes = header.classes or {}
    table.insert(header.classes, "unnumbered")
    table.insert(header.classes, "toc-heading")
    return header
  end
  return nil
end
