-- fix_title_and_toc.lua
-- 1) strip leading "title:" tokens from Paras and Headers
-- 2) remove embedded DOCX TOC Divs (custom-style="toc ...") to avoid duplicate TOC when using --toc
-- 3) normalize TOC heading: mark as unnumbered and add class "toc-heading"
-- 4) convert BulletList inside TOC Div to OrderedList if we keep a TOC block
-- 5) preserve heading numbering (skip TOC/Abstract/Preface and unnumbered classes)

local utils = pandoc.utils
local counts = {0,0,0,0,0,0}

local function lower(s) if not s then return "" end return s:lower() end

-- Detect strings that look like TOC heading
local function looks_like_toc_text(s)
  s = lower(s)
  return s:find("table of contents") or s:find("^contents$") or s:find("^toc$")
end

-- Detect unnumbered classes
local function is_unnumbered_class(el)
  if not el.classes then return false end
  for _,c in ipairs(el.classes) do
    local lc = lower(c)
    if lc == "unnumbered" or lc == "no-number" or lc == "no_number" or lc == "toc-heading" then
      return true
    end
  end
  return false
end

-- Detect if header already starts with a number token
local function already_numbered(el)
  local s = utils.stringify(el.content)
  s = s:match("^%s*(.-)$") or s
  return s:match("^%d+[%.)]") or s:match("^%d+[%d%.]*%s+")
end

-- Remove leading "title:" token (case-insensitive) from a string
local function strip_title_token_from_string(s)
  if not s then return s end
  local trimmed = s:gsub("^%s+", ""):gsub("%s+$", "")
  local low = lower(trimmed)
  local m = low:match("^title%s*:")
  if m then
    -- find the colon position in original trimmed string and return remainder
    local colon_pos = trimmed:find(":")
    if colon_pos then
      return trimmed:sub(colon_pos + 1):gsub("^%s+", "")
    end
  end
  return s
end

-- Convert BulletList to OrderedList starting at 1 (preserve nested structure)
local function bullet_to_ordered(bullet)
  local ordered_items = {}
  for i, item in ipairs(bullet) do
    ordered_items[i] = item
  end
  return pandoc.OrderedList(1, ordered_items)
end

-- Heuristic: detect embedded DOCX TOC Div by custom-style attribute or class containing "toc"
local function is_embedded_docx_toc(div)
  if div.t ~= "Div" then return false end
  local attr = div.attr or {}
  local classes = attr.classes or {}
  for _,c in ipairs(classes) do
    if lower(c):find("toc") then return true end
  end
  if attr.attributes then
    for k,v in pairs(attr.attributes) do
      if lower(k):find("toc") then return true end
      if type(v) == "string" and lower(v):find("toc") then return true end
    end
  end
  -- fallback: stringify and look for "Table of Contents" phrase
  if utils.stringify(div):lower():find("table of contents") then return true end
  return false
end

-- Pandoc hook: run once over the whole document to remove embedded TOC Divs and normalize title tokens
function Pandoc(doc)
  local blocks = doc.blocks
  local new_blocks = {}
  local seen_embedded_toc = false

  for i, blk in ipairs(blocks) do
    -- Strip "title:" token from Paras
    if blk.t == "Para" then
      local s = utils.stringify(blk)
      local stripped = strip_title_token_from_string(s)
      if stripped ~= s then
        blk = pandoc.Para({pandoc.Str(stripped)})
      end
    end

    -- Strip "title:" token from Headers
    if blk.t == "Header" then
      local s = utils.stringify(blk)
      local stripped = strip_title_token_from_string(s)
      if stripped ~= s then
        blk.content = { pandoc.Str(stripped) }
      end
      -- If header has Title/Subtitle classes, mark as unnumbered to avoid numbering
      if blk.classes then
        for _,c in ipairs(blk.classes) do
          local lc = lower(c)
          if lc == "title" or lc == "doc-title" or lc == "subtitle" or lc == "toc-heading" then
            blk.classes = blk.classes or {}
            table.insert(blk.classes, "unnumbered")
            if lc == "toc-heading" then
              -- ensure it's visually distinct: keep class toc-heading
              table.insert(blk.classes, "toc-heading")
            end
            break
          end
        end
      end
    end

    -- Handle embedded DOCX TOC Divs
    if is_embedded_docx_toc(blk) then
      -- If user passed --toc, prefer Pandoc-generated TOC: drop embedded DOCX TOC
      -- Keep only the first embedded TOC if you want to preserve it; here we drop all to avoid duplication
      seen_embedded_toc = true
      -- skip adding this block (effectively removing embedded TOC)
    else
      -- If this block is a Div that contains a BulletList that looks like a TOC (rare), convert it
      if blk.t == "Div" and blk.content then
        for j, inner in ipairs(blk.content) do
          if inner.t == "BulletList" then
            -- convert to ordered list to avoid bullets in TOC-like lists
            blk.content[j] = bullet_to_ordered(inner)
          end
          if inner.t == "Header" and looks_like_toc_text(utils.stringify(inner)) then
            inner.classes = inner.classes or {}
            table.insert(inner.classes, "toc-heading")
            table.insert(inner.classes, "unnumbered")
            inner.level = 1
            blk.content[j] = inner
          end
        end
      end
      table.insert(new_blocks, blk)
    end
  end

  return pandoc.Pandoc(new_blocks, doc.meta)
end

-- Header numbering: skip TOC/Abstract/Preface and unnumbered classes; avoid leading zeros
function Header(el)
  local header_text = utils.stringify(el.content):lower()

  if looks_like_toc_text(header_text) or header_text:find("abstract") or header_text:find("preface") or is_unnumbered_class(el) then
    return el
  end

  if already_numbered(el) then
    return el
  end

  -- increment counter for this level
  counts[el.level] = counts[el.level] + 1
  -- reset deeper levels
  for i = el.level + 1, 6 do counts[i] = 0 end

  -- build number string from non-zero counters up to current level
  local parts = {}
  for i = 1, el.level do
    if counts[i] and counts[i] > 0 then table.insert(parts, tostring(counts[i])) end
  end
  local num_string = ""
  if #parts > 0 then num_string = table.concat(parts, ".") .. ". " end

  if num_string ~= "" then
    table.insert(el.content, 1, pandoc.Str(num_string))
  end

  return el
end
