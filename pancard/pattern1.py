
class PanCardPattern1:
    def __init__(self, coordinates, text, matching_text) -> None:
        self.coordinates = coordinates
        self.text = text
        self.matching_text = matching_text

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

        # find the line that matches search text in coordinates
        matching_text_index = self.__find_matching_text_index(self.matching_text, self.coordinates)
        if matching_text_index == 0:
            return matching_text_coords
        
        # find the line that matches search text
        matching_line_index = self.__find_matching_line_index(lines, self.matching_text)
        if matching_line_index == 0:
            return matching_text_coords

        # get the next line in the text
        for line in lines[matching_line_index + 1 :]:
            if len(line) != 0:
                next_line_list = line.split()
                break
        
        if len(next_line_list) > 1:
            next_line_list = next_line_list[:-1]

        # get the matching next line text coordinates
        for i in range(matching_text_index, len(self.coordinates)):
            if self.coordinates[i][4] in next_line_list:
                matching_text_coords.append([self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]])
            if len(matching_text_coords) == len(next_line_list):
                return matching_text_coords

    def __find_matching_text_index(self, matching_text: list, coords: list) -> int:
        # find the line that matches search text in coordinates
        for i, (x1, y1, x2, y2, text) in enumerate(coords):
            if text in matching_text:
                return i
        return 0

    def __find_matching_line_index(self, lines: list, matching_text: list ) -> int:
        # find the line that matches search text
        for i,line in enumerate(lines):
            for k in matching_text:
                if k in line:
                    return i
        return 0