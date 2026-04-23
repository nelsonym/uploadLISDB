-- clean_lists.lua
-- Normalize list items coming from DOCX custom-style wrappers.

local function flatten_div_blocks(blocks)
  local output = {}
  for _, block in ipairs(blocks) do
    if block.t == "Div" then
      for _, inner in ipairs(block.content) do
        table.insert(output, inner)
      end
    else
      table.insert(output, block)
    end
  end
  return output
end

function BulletList(list)
  local cleaned = {}
  for i, item in ipairs(list.content) do
    cleaned[i] = flatten_div_blocks(item)
  end
  return pandoc.BulletList(cleaned)
end

function OrderedList(list)
  local cleaned = {}
  for i, item in ipairs(list.content) do
    cleaned[i] = flatten_div_blocks(item)
  end
  return pandoc.OrderedList(cleaned, list.listAttributes)
end
