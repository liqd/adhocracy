from pylons import tmpl_context as c

from util import render_tile, BaseTile


class VariantRow(object):
    
    def __init__(self, tile, variant, poll):
        self.tile = tile
        self.variant = variant
        self.poll = poll
        if tile.selection.proposal.is_adopt_polling():
            freeze_time = tile.selection.proposal.adopt_poll.begin_time
            self.text = tile.selection.page.variant_at(variant, freeze_time)
        else:
            self.text = tile.selection.page.variant_head(variant)
            
    
    @property
    def selected(self):
        return self.tile.selected == self.variant
    
    
    @property
    def num_comments(self):
        return len(self.tile.selection.page.variant_comments(self.variant))
    
    

class SelectionTile(BaseTile):
    
    def __init__(self, selection, max_variants=None):
        self.selection = selection
        self.max_variants = max_variants
        self.selected = selection.selected
        self.variant_polls = self.selection.variant_polls
        
    
    @property
    def has_variants(self):
        return len(self.selection.page.variants) < 2
        
        
    def variant_rows(self):
        num = 0
        for (variant, poll) in self.variant_polls:
            row = VariantRow(self, variant, poll)
            yield row
            num += 1
            if self.max_variants and num >= self.max_variants:
                break
        
        
    @property
    def show_more_link(self):
        return self.max_variants and len(self.variant_polls) > self.max_variants

        

def full(selection, max_variants=None):
    tile = SelectionTile(selection, max_variants=max_variants)
    return render_tile('/selection/tiles.html', 'full', tile, 
                       selection=selection)