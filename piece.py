import numpy as np

#keeps all of the masks associated with one of the 21 pieces
#the top left corner is (0,0) for all masks, even if there is a gap in the piece there
class Piece:
    def __init__(self, id, value, area_mask, adj_mask, diag_mask):
        self.id = id
        self.value = value
        self.area_masks = []
        self.adj_masks = []
        self.diag_masks = []
        self.diag_locs = [[None for _ in range(4)] for _ in range(8)]
        self.unique_ors = []

        #generate all 8 orientations
        for _ in range(4):
            self.area_masks.append(np.copy(area_mask))
            self.adj_masks.append(np.copy(adj_mask))
            self.diag_masks.append(np.copy(diag_mask))
            area_mask = np.rot90(area_mask)
            adj_mask = np.rot90(adj_mask)
            diag_mask = np.rot90(diag_mask)
        area_mask = np.flip(area_mask,1)
        adj_mask = np.flip(adj_mask,1)
        diag_mask = np.flip(diag_mask,1)
        for _ in range(4):
            self.area_masks.append(np.copy(area_mask))
            self.adj_masks.append(np.copy(adj_mask))
            self.diag_masks.append(np.copy(diag_mask))
            area_mask = np.rot90(area_mask)
            adj_mask = np.rot90(adj_mask)
            diag_mask = np.rot90(diag_mask)

        #determine which orientations are unique
        unique_masks = []
        for i in range(len(self.area_masks)):
            candidate = self.area_masks[i]
            unique = True
            for mask in unique_masks:
                unique = unique and (not np.all(mask == candidate))
            if unique:
                self.unique_ors.append(i)
                unique_masks.append(candidate)

        #get locations with adjacent corners
        padding_shapes = (((0,2),(2,0)),
                          ((0,2),(0,2)),
                          ((2,0),(0,2)),
                          ((2,0),(2,0)))
        reverse_shift = ((0,-2),(0,0),(-2,0),(-2,-2))
        for i in range(len(self.area_masks)):
            area = self.area_masks[i]
            diag = self.diag_masks[i]
            for j in range(4):
                padded_area = np.pad(area,padding_shapes[j],'constant')
                selected = np.logical_and(padded_area,diag)
                row,col = np.where(selected)
                self.diag_locs[i][j] = [(row[k]+reverse_shift[j][0],col[k]+reverse_shift[j][1]) for k in range(len(row))]

    def print_piece(self, piece_or, player_id):
        print(str((player_id+1)*(np.array(self.area_masks[piece_or], dtype=np.uint8))) + '\n')


#reads all of the different piece shapes from a file
#only call this ONCE, even if many games are played
#it's pretty expensive
def read_pieces(file_name):
    read_file = open(file_name, 'r')
    areas = []
    pieces = []
    curr_area = []

    for line in read_file:
        tokens = line.split()
        if not tokens:
            if curr_area:
                areas.append(np.array(curr_area, dtype=np.bool))
                curr_area = []
        else:
            curr_area.append([bool(int(tokens[0][i])) for i in range(len(tokens[0]))])
    if curr_area:
        areas.append(np.array(curr_area, dtype=np.bool))
    read_file.close()

    for i in range(len(areas)):
        curr_area = areas[i]
        area_shape = np.shape(curr_area)
        curr_adj = np.zeros((area_shape[0]+2,area_shape[1]+2), dtype=np.bool)
        curr_diag = np.zeros((area_shape[0]+2,area_shape[1]+2), dtype=np.bool)
        for row in range(len(curr_area)):
            for col in range(len(curr_area[row])):
                if curr_area[row][col] == True:
                    curr_adj[row+1][col] = True
                    curr_adj[row+1][col+2] = True
                    curr_adj[row][col+1] = True
                    curr_adj[row+2][col+1] = True
                    curr_diag[row][col] = True
                    curr_diag[row+2][col] = True
                    curr_diag[row][col+2] = True
                    curr_diag[row+2][col+2] = True
        padded_area = np.zeros(np.shape(curr_adj), dtype=np.bool)
        padded_area[1:np.shape(curr_area)[0]+1,1:np.shape(curr_area)[1]+1] = curr_area
        curr_diag = np.logical_and(curr_diag, np.logical_not(curr_adj))
        curr_diag = np.logical_and(curr_diag, np.logical_not(padded_area))
        curr_adj = np.logical_and(curr_adj, np.logical_not(padded_area))
        pieces.append(Piece(i,np.count_nonzero(curr_area),curr_area,curr_adj,curr_diag))
    return pieces


#print out pieces for debugging purposes
def print_pieces(pieces):
    for piece in pieces:
        print ("Piece " + str(piece.id) + ", value " + str(piece.value))
        print ("Area Masks:")
        for mask in piece.area_masks:
            print(np.array(mask, dtype=np.uint8))
        print("Adj Masks:")
        for mask in piece.adj_masks:
            print(np.array(mask, dtype=np.uint8))
        print("Diag Masks:")
        for mask in piece.diag_masks:
            print(np.array(mask, dtype=np.uint8))
        print("Diag Points:")
        for i in range(8):
            for j in range(4):
                print("Quadrant " + str(j+1) + ": " + str(piece.diag_locs[i][j]))
        print("Unique Orientations:")
        print(piece.unique_ors)
        print("")