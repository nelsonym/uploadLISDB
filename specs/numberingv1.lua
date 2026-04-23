-- numberingv1.lua
-- Preserve Word layout exactly:
--  - Convert Title-style paragraph into a Header(1) in the body (no "title:" YAML or literal)
--  - Remove embedded DOCX TOC Divs (avoid duplicate TOC and bullet artifacts)
--  - Preserve list semantics (do not add bullets where Word had none)
--  - Keep heading numbering logic (skip unnumbered/TOC/Abstract/Preface)

local utils = pandoc.utils
local counts = {0,0,0,0,0,0}

local function lower(s) if not s then return "" end return s:lower() end

local function looks_like_toc_text(s)
  s = lower(s)
  return s:find("table of contents") or s:find("^contents$") or s:find("^toc$")
end

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

local function already_numbered(el)
  local s = utils.stringify(el.content)
  s = s:match("^%s*(.-)$") or s
  return s:match("^%d+[%.)]") or s:match("^%d+[%d%.]*%s+")
end

-- Detect embedded DOCX TOC Div by class/custom-style/attributes or content
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
  if utils.stringify(div):lower():find("table of contents") then return true end
  return false
end

-- Strip any leading literal "title:" token from a string (defensive)
local function strip_leading_title_token(s)
  if not s then return s end
  local trimmed = s:gsub("^%s+", ""):gsub("%s+$", "")
  if lower(trimmed):match("^title%s*:") then
    local colon = trimmed:find(":")
    if colon then
      return trimmed:sub(colon+1):gsub("^%s+", "")
    end
  end
  return s
end

-- Track list nesting so we preserve list items exactly
local list_depth = 0
function BulletList(el)
  list_depth = list_depth + 1
  local res = el
  list_depth = list_depth - 1
  return res
end
function OrderedList(el)
  list_depth = list_depth + 1
  local res = el
  list_depth = list_depth - 1
  return res
end

-- Pandoc hook: normalize Title style into Header(1), remove embedded DOCX TOC Divs,
-- remove any literal "title:" paragraph/header, and ensure no metadata title is emitted.
function Pandoc(doc)
  local blocks = doc.blocks
  local new_blocks = {}

  -- 1) Walk blocks and convert any block with class "Title" into Header(1)
  --    and remove any leading literal "title:" paragraphs/headers.
  for i = 1, #blocks do
    local blk = blocks[i]

    -- Defensive: remove any leading Para/Header that literally starts with "title:"
    if (blk.t == "Para" or blk.t == "Header") then
      local s = utils.stringify(blk):gsub("^%s+", "")
      if lower(s):match("^title%s*:") then
        -- skip this block entirely (do not emit)
        goto continue
      end
    end

    -- If block has Title style class, convert to Header(1) and emit (do not set metadata)
    if (blk.t == "Para" or blk.t == "Header") and blk.classes then
      for _,c in ipairs(blk.classes) do
        if lower(c) == "title" or lower(c) == "doc-title" then
          -- convert to Header level 1, preserve inline content
          local content = blk.content or {}
          local hdr = pandoc.Header(1, content, blk.attr)
          -- mark as unnumbered so numbering filter won't number it
          hdr.classes = hdr.classes or {}
          table.insert(hdr.classes, "unnumbered")
          table.insert(new_blocks, hdr)
          goto continue
        end
      end
    end

    -- Remove embedded DOCX TOC Divs to avoid duplicate TOC when using --toc
    if is_embedded_docx_toc(blk) then
      -- skip it
      goto continue
    end

    -- Otherwise keep the block as-is
    table.insert(new_blocks, blk)
    ::continue::
  end

  -- 2) Ensure we do NOT emit a metadata title in YAML (user asked no "title:" added)
  local meta = doc.meta or pandoc.Meta({})
  meta.title = nil

  return pandoc.Pandoc(new_blocks, meta)
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

  counts[el.level] = counts[el.level] + 1
  for i = el.level + 1, 6 do counts[i] = 0 end

  local parts = {}
  for i = 1, el.level do
    if counts[i] and counts[i] > 0 then table.insert(parts, tostring(counts[i])) end
  end
  local num_string = ""
  if #parts > 0 then num_string = table.concat(parts, ".") .. ". " end
  if num_string ~= "" then table.insert(el.content, 1, pandoc.Str(num_string)) end

  return el
end

-- Paragraphs: preserve list paragraphs exactly; do not add bullets or convert non-list paragraphs into lists
function Para(el)
  -- If inside a list, preserve exactly
  if list_depth and list_depth > 0 then return el end

  -- If style/class indicates list paragraph, preserve
  if el.classes then
    for _,c in ipairs(el.classes) do
      local lc = lower(c)
      if lc:find("list") or lc:find("listparagraph") or lc:find("bullet") or lc:find("number") then
        return el
      end
    end
  end

  -- Defensive: strip any accidental leading "title:" token inside a paragraph
  local s = utils.stringify(el):gsub("^%s+", "")
  if lower(s):match("^title%s*:") then
    -- convert to a normal paragraph without the token
    local stripped = strip_leading_title_token(s)
    return pandoc.Para({pandoc.Str(stripped)})
  end

  return el
end

-- Table: preserve header inline formatting and nested lists inside cells (do not add bullets)
function Table(tbl)
  -- do not alter table structure; keep captions and inline formatting
  return tbl
end
