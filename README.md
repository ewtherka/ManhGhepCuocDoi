# Mảnh ghép cuộc đời
 Trò chơi được xây dựng dựa trên MATCH3PY của tác giả Tomas Gonzalez Aragon và lấy ý tưởng từ Life Crush Story của QuickTurtle.\
 Nhóm sinh viên thực hiện:
 - Trịnh Nguyễn Cát Tường (25522036)
 - Đỗ Hải Yến (25522133)
 - Nguyễn Khánh Vân (25522051)\
Giảng viên hướng dẫn: Thạc sĩ Phạm Nguyễn Trường An\
Trân trọng cảm ơn thầy vì đã hết lòng chỉ dạy chúng em.

# Tổng quan

"Mảnh Ghép Cuộc Đời" là một tựa game giải đố ghép ba (Match-3) kết hợp với yếu tố mô phỏng vòng đời con người. Trò chơi tái hiện lại hành trình của một cá nhân từ lúc sinh ra, trưởng thành cho đến khi theo đuổi ước mơ. Thông qua việc tư duy và thao tác trên bảng giải đố, người chơi sẽ trực tiếp định hình tương lai và quyết định số phận của nhân vật.

# Cơ chế lối chơi

Gameplay chính xoay quanh việc hoán đổi vị trí các khối vuông để tạo thành chuỗi tương đồng (match), với mỗi loại khối đại diện cho các yếu tố trong cuộc sống.

# Nhân vật

**Tiến trình phát triển (Các giai đoạn cuộc đời):** Vòng đời của nhân vật được thiết kế theo trình tự tuyến tính gồm 5 giai đoạn: Sơ sinh, Thiếu nhi, Thiếu niên, Thanh niên và Trưởng thành. Khi thanh thời gian đạt mức tối đa, nhân vật sẽ tự động tiến vào giai đoạn tiếp theo. Trò chơi sẽ kết thúc khi giai đoạn "Trưởng thành" hoàn tất hoặc người chơi đạt đủ điều kiện để tiến đến Ending.

**Định hướng Số phận (Kết cục/Ending):** Tương lai của nhân vật là hệ quả trực tiếp từ quá trình trải nghiệm của người chơi. Khi người chơi đạt đủ điều kiện (Đạt chỉ số và chiến thắng minigame), trò chơi lập tức tiến đến Ending. Ngoài ra, khi kết thúc giai đoạn trưởng thành mà chưa thỏa điều kiện, hệ thống sẽ tổng hợp đánh giá dựa trên các chỉ số mà nhân vật đã tích lũy được để quyết định Số phận cuối cùng (Ending) của nhân vật đó.

# Khối

**Khối CLOCK:** Đại diện cho tiến trình trưởng thành. Khi người chơi ghép thành công khối này, điểm sẽ được cộng vào Thanh thời gian. Lúc thanh này đạt mức tối đa, nhân vật sẽ chuyển sang giai đoạn cuộc đời tiếp theo và Thanh thời gian được thiết lập lại từ đầu.

**Khối HOBBY:** Chi phối định hướng cá nhân của nhân vật thông qua 3 cấp độ: "Trống", "Thú vui" và "Đam mê". Khi tích lũy đủ điểm để đạt mốc "Thú vui", nhân vật sẽ mở khóa một lĩnh vực ngẫu nhiên để theo đuổi. Khi hoàn tất mốc "Đam mê", người chơi tiến vào một minigame quyết định: chiến thắng sẽ lập tức kích hoạt Kết cục (Ending), trong khi thất bại sẽ đưa chỉ số về lại đầu giai đoạn "Đam mê" và trò chơi tiếp diễn với một Kết cục khác.

**Khối CHANCE:** Đại diện cho những biến số bất ngờ, vận hành qua 2 cấp độ: "Trống" và "Cơ hội". Khi chạm mốc "Cơ hội", một sự kiện ngẫu nhiên sẽ phát sinh. Khi kết thúc giai đoạn này, người chơi sử dụng "Vòng quay may mắn" để xác định kết quả: ô "FAILED" sẽ đưa hệ thống về lại mốc "Cơ hội" để tiếp tục trò chơi; các ô kết quả khác sẽ ngay lập tức kết thúc hành trình và hiển thị Kết cục tương ứng.

**Khối BOOST:** Được tạo ra khi ghép thành công chuỗi 4 khối cùng loại. Khối này tự động xuất hiện ở vị trí dưới cùng, bên phải của dải ô vừa bị triệt tiêu. Chức năng chính của khối là khuếch đại điểm số, giúp tăng gấp đôi giá trị điểm của bản thân ở lượt thao tác sau.

**Khối FATE:** Hình thành khi người chơi ghép thành công một chuỗi 5 khối trở lên, độc lập và không thể được ghép với các khối khác. Bằng cách kích hoạt khối này, người chơi được quyền rút một "Thẻ định mệnh" ngẫu nhiên mang các hiệu ứng đặc biệt, sau đó khối sẽ tự động xóa khỏi bàn chơi.

CHƯƠNG 2: CHỨC NĂNG VÀ CÁCH HOẠT ĐỘNG

# Chức năng match khối

**Match 3:** Khi xếp 3 khối cùng loại thẳng hàng (ngang hoặc dọc). Hệ thống sẽ xóa 3 hạt, cộng điểm tích lũy cho khối tương ứng và kích hoạt hiệu ứng các khối rơi xuống để bù vào khoảng trống đã xóa.

**Match 4:** Khi xếp 4 khối cùng loại thẳng hàng, hệ thống sẽ xóa đi 3 khối trong hàng (xóa 3 khối bên trái nếu là hàng ngang và xóa 3 khối phía trên nếu là hàng dọc), một khối sẽ được nâng cấp lên thành khối Boost. Số điểm của việc match 4 khối hay match 3 khối có khối Boost sẽ cao hơn số điểm match 3 khối bình thường, khoảng trống đã xóa cũng sẽ được lấp đầy bởi hiệu ứng rơi xuống của các khối trên nó.

**Match 5 khối trở lên:** Khi xếp được từ 5 khối trở lên cùng loại thẳng hàng, hệ thống sẽ tạo thành một khối Fate, cho phép người chơi sử dụng hiệu ứng đặc biệt ngẫu nhiên. Sau đó, hệ thống thực hiện xóa và lấp đầy khoảng trống bằng hiệu ứng rơi xuống của các khối phía trên.

# Chức năng sinh trưởng của nhân vật

Vòng đời của nhân vật được thiết kế theo 5 giai đoạn khác nhau: Sơ sinh - Thiếu nhi - Thiếu niên - Thanh niên - Trưởng thành. Tiến trình này được biểu diễn qua thanh thời gian hình đồng hồ cát. Khi người chơi tích lũy điểm và làm thanh thời gian đạt mức tối đa, nhân vật sẽ tự động tiến hóa sang giai đoạn cuộc đời tiếp theo. Trò chơi sẽ kết thúc khi giai đoạn "Trưởng thành" hoàn tất hay người chơi đạt đủ điều kiện để tiến thẳng đến kết cục của nhân vật.

# Minigame

Khi số điểm của khối Hobby hoặc khối Chance đạt đến một mức độ nhất định, người chơi sẽ hoàn thành Minigame để quyết định số phận của nhân vật. Đồ án có 4 minigame chính:

- Tailor: là một thử thách dạng phản xả nhanh, xuất hiện khi người chơi đạt được mức độ tối đa của nghề thợ may trong khối Hobby. Trong minigame này, người chơi có nhiệm vụ quan sát một cây kim di chuyển liên tục qua lại trên một thanh ngang và thực hiện thao tác click chuột đúng thời điểm cây kim nằm gọn trong khu vực mục tiêu để giành chiến thắng. Nếu thắng, người chơi sẽ có kết cục là trở thành thợ may hoàng gia. Nếu thua, người chơi sẽ bị giáng chức làm thợ may bình thường và phải đạt điểm tối đa khối Hobby lần nữa để có được kết cục này.
- Fighter: là một thử thách dạng đánh quái thu thập điểm, xuất hiện một cách ngẫu nhiên. Trong minigame này, người chơi có nhiệm vụ di chuyển nhân vật bằng các phím W, S, A, D để đi theo các hướng trên, dưới, trái, phải. Click chuột trái để nhân vật làm hành động vung kiếm. Những con quái vật sẽ xuất hiện ở vị trí ngẫu nhiên và đi về phía nhân vật. Khi đó, người chơi cần vừa di chuyển né đòn đánh của quái, vừa thực hiện đánh quái để đạt được số điểm nhất định hoàn thành thử thách.
- Minesweeper: là thử thách dò mìn. Nhiệm vụ của người chơi là mở hết những ô không có mìn, né những ô có mìn để chiến thắng. Quy luật là khi mở một ô sẽ có một con số cụ thể, con số đó sẽ báo hiệu số mìn trong bán kính 1 ô xung quanh nó. Nếu người chơi hoàn thành mở hết những ô không chứa mìn thì người chơi chiến thắng thử thách và nhận được kết cục tốt.
- SlotMachine: là thử thách mô phỏng vòng quay may mắn dạng cuộn đơn, xuất hiện khi khối Chance đạt được số điểm nhất định. Đây là một minigame dựa trên nhân phẩm của người chơi, trong đó các phần thưởng trôi dọc theo màn hình ở tốc độ cao và người chơi cần bấm dừng để nhận được kết quả ngẫu nhiên.

# Khối Fate

Được hình thành khi ghép được chuỗi 5 khối cùng loại trở lên, có chức năng kích hoạt một trong những hiệu ứng đặc biệt:

- Thanh thời gian đứng yên trong hai lượt đi tiếp theo.
- Thu thập tất cả khối Chance có trên bàn cờ.
- Nhân đôi số điểm nhận được của khối Hobby trong hai lượt tiếp theo.
- Mất 5 điểm tích lũy của khối Hobby.
- Mất 5 điểm tích lũy của khối Chance.
- Số điểm của thanh thời gian được nhân gấp đôi trong hai lượt tiếp theo.

# Chức năng Hint

Được thiết kế theo hình dấu "?", nhiệm vụ của chức năng này là gợi ý khối có thể đổi vị trí để tạo nên match 3, 4 hay 5 trở lên. Người chơi có thể sử dụng chức năng này khi không nhìn ra được nước đi phù hợp.

## Prerequisites
* [Python](https://www.python.org/downloads) `>=3.9.0`
* [Pygame](https://pypi.org/project/pygame) `>=2.0.0`
* [Pygame Widgets](https://pypi.org/project/pygame-widgets) `>=0.6.0`
* [jsonschema](https://pypi.org/project/jsonschema) `>=3.2.0`

## Running
Vui lòng đảm bảo rằng pip và python đã được tải và thêm vào enviroment variable.

Chạy trò chơi bằng cách dán lệnh sau vào Command Prompt:

`python ManhGhepCuocDoi.pyw`
