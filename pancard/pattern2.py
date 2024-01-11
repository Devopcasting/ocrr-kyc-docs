import re

class PanCardPattern2:
    def __init__(self,  coordinates, text, matching_text, index_num) -> None:
        self.coordinates = coordinates
        self.text = text
        self.matching_text = matching_text
        self.index_num = index_num

    # func: extract pan card user name and father name
    def search_coordinates_user_father_name(self) -> list:
        """
            Search the coordinates first line below matching text in an image using OCR.
            Args:
                matching_text: The text to match.
            Returns:
                The list of coordinates of the first line below matching text found.
        """
        # split the text into lines.
        lines = [i for i in self.text.splitlines() if len(i) != 0]
      
        # define : matching text coordinates
        matching_text_coords = []

        # find the line that matches search text
        matching_line_index = self.__find_matching_line_index(lines, self.matching_text)
        if matching_line_index == 404:
            return matching_text_coords
        
        # get the next line in the text
        for line in lines[matching_line_index + self.index_num :]:
            if line != 'GOVT. OF INDIA':
                next_line_list = line.split()
                break

        # remove special characters and white spaces
        clean_next_line = [element for element in next_line_list if re.search(r'[a-zA-Z0-9]', element)]
        if len(clean_next_line) > 1:
            clean_next_line = clean_next_line[:-1]
            
        # get the coordinates
        for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
            if text in clean_next_line:
                matching_text_coords.append([x1, y1, x2, y2])
            if len(matching_text_coords) == len(clean_next_line):
                return matching_text_coords
       
    
    def __find_matching_line_index(self, lines: list, matching_text: list) -> int:
        # find the line that matches search text
        for i,line in enumerate(lines):
            for k in matching_text:
                if k in line:
                    return i
        return 404