-- normalize_styles.lua
-- Normalize title/subtitle/custom style wrappers for cleaner markdown.

local utils = pandoc.utils

local function lower(value)
  if not value then
    return ""
  end
  return tostring(value):lower()
end

local function strip_title_token(text)
  local trimmed = text:gsub("^%s+", ""):gsub("%s+$", "")
  local lowered = lower(trimmed)
  if lowered:match("^title%s*:") then
    local colon_pos = trimmed:find(":")
    if colon_pos then
      return trimmed:sub(colon_pos + 1):gsub("^%s+", "")
    end
  end
  return text
end

local function has_class(el, class_name)
  for _, c in ipairs(el.classes or {}) do
    if lower(c) == lower(class_name) then
      return true
    end
  end
  return false
end

function Para(para)
  local text = utils.stringify(para)
  local stripped = strip_title_token(text)
  if stripped ~= text then
    return pandoc.Para({ pandoc.Str(stripped) })
  end
  return nil
end

function Header(header)
  local text = utils.stringify(header.content)
  local stripped = strip_title_token(text)
  if stripped ~= text then
    header.content = { pandoc.Str(stripped) }
  end

  if has_class(header, "title") or has_class(header, "subtitle") or has_class(header, "toc-heading") then
    header.classes = header.classes or {}
    table.insert(header.classes, "unnumbered")
  end
  return header
end

function Div(div)
  -- Flatten custom style wrappers that only carry a style name.
  if (div.attr and div.attr.attributes and div.attr.attributes["custom-style"]) or
     (div.attr and div.attr.attributes and div.attr.attributes["data-custom-style"]) then
    return div.content
  end
  return nil
end
