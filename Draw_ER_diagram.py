import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QBrush, QPolygonF
import json
#jbqt的画板和pygame是反的，他是最先绘画的在最上层显示，被这个坑了好久

class mainGui(QWidget):
    def __init__(self, ermap):
        super().__init__()
        self.ermap = ermap
        self.initUI()

    def initUI(self):
        self.setWindowTitle("ER图绘制")
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, int(screen.width() * 0.8), int(screen.height() * 0.8))
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

        self.ermap.initialization()
        self.addCoordinates()

        self.showHelpDialog()
        self.show()

    def addCoordinates(self):
        for i, entity in enumerate(self.ermap.entity):
            if 'x' not in entity or 'y' not in entity or 'attribute_coords' not in entity:
                entity['x'] = 100 + i * 200
                entity['y'] = 100 + i * 150
                entity['attribute_coords'] = [[entity['x'] + 50, entity['y'] + 75] for _ in entity['attribute']]
    
        for i, contact in enumerate(self.ermap.contact):
            if 'x' not in contact or 'y' not in contact or 'attribute_coords' not in contact:
                contact['x'] = 150 + i * 200
                contact['y'] = 150 + i * 150
                contact['attribute_coords'] = [[contact['x'] + 50, contact['y'] + 75] for _ in contact['attribute']]

    def showHelpDialog(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Help')
        msg_box.setText('单击S可以将当前的坐标信息也一同保存下来\n点击键盘h会再次弹出提示框\n点击ctrl加s会将当前这个窗口的内容保存为一张图像\n直接鼠标左键可以拖动属性和实体\nshift加鼠标左键把属性和实体一起移动\nalt加鼠标左键可以移动画布')
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setStyleSheet("QLabel{min-width: 600px; min-height: 400px;}")
        msg_box.exec_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
    
        # 先绘制联系的线条
        for contact in self.ermap.contact:
            self.drawContactLines(painter, contact)
    
        # 再绘制实体
        for entity in self.ermap.entity:
            self.drawEntity(painter, entity)
    
        # 最后绘制联系
        for contact in self.ermap.contact:
            self.drawContact(painter, contact)

    def drawEntity(self, painter, entity):
        for i, attr in enumerate(entity.get('attribute', [])):
            self.drawAttribute(painter, attr, entity['attribute_coords'][i], (entity['x'], entity['y']))
    
        rect = QRectF(entity['x'], entity['y'], 100, 50)
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(Qt.white))
        painter.drawRect(rect)
        painter.drawText(rect, Qt.AlignCenter, entity['name'])
    
        # Draw normal line for primary key attribute
        if isinstance(entity['primaryKey'], int):
            primary_key_index = entity['primaryKey']
            primary_key_coords = entity['attribute_coords'][primary_key_index]
            attr_x, attr_y = primary_key_coords
            parent_x, parent_y = entity['x'], entity['y']
    
            # Calculate midpoint of the line
            mid_x = (attr_x + 50 + parent_x + 50) / 2
            mid_y = (attr_y + parent_y + 25) / 2
    
            # Calculate the angle of the line
            dx = (attr_x + 50) - (parent_x + 50)
            dy = attr_y - (parent_y + 25)
            length = (dx**2 + dy**2)**0.5
            if length == 0:
                length = 1  # Avoid division by zero
            unit_dx = dx / length
            unit_dy = dy / length
    
            # Calculate the perpendicular vector
            perp_dx = -unit_dy
            perp_dy = unit_dx
    
            # Draw normal line
            painter.setPen(QPen(Qt.black, 2))
            painter.drawLine(QPointF(mid_x + perp_dx * 10, mid_y + perp_dy * 10), QPointF(mid_x - perp_dx * 10, mid_y - perp_dy * 10))

    def drawAttribute(self, painter, attr, coords, parent_coords):
        if not attr.strip():  # 检测属性是否为空字符串
            return
        
        attr_x, attr_y = coords
        parent_x, parent_y = parent_coords
    
        # Draw line connecting attribute to parent
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(QPointF(attr_x + 50, attr_y), QPointF(parent_x + 50, parent_y + 25))
    
        ellipse = QRectF(attr_x, attr_y, 100, 50)
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(Qt.white))
        painter.drawEllipse(ellipse)
        painter.drawText(ellipse, Qt.AlignCenter, attr)

    def drawContact(self, painter, contact):
        for i, attr in enumerate(contact.get('attribute', [])):
            self.drawAttribute(painter, attr, contact['attribute_coords'][i], (contact['x'], contact['y']))

        center_x = contact['x'] + 50
        center_y = contact['y'] + 25
        diamond = [
            QPointF(center_x, center_y - 25),
            QPointF(center_x + 50, center_y),
            QPointF(center_x, center_y + 25),
            QPointF(center_x - 50, center_y)
        ]
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(Qt.white))
        painter.drawPolygon(diamond)
        painter.drawText(QRectF(contact['x'], contact['y'], 100, 50), Qt.AlignCenter, contact['name'])

    def drawContactLines(self, painter, contact):
        entity1 = next(e for e in self.ermap.entity if e['name'] == contact['twoEntities'][0])
        entity2 = next(e for e in self.ermap.entity if e['name'] == contact['twoEntities'][1])
    
        line_start = QPointF(entity1['x'] + 50, entity1['y'] + 25)
        line_end = QPointF(entity2['x'] + 50, entity2['y'] + 25)
        contact_center = QPointF(contact['x'] + 50, contact['y'] + 25)
    
        painter.drawLine(line_start, contact_center)
        painter.drawLine(contact_center, line_end)
    
        # Draw cardinality
        cardinality_start = QPointF((line_start.x() + contact_center.x()) / 2, (line_start.y() + contact_center.y()) / 2)
        cardinality_end = QPointF((line_end.x() + contact_center.x()) / 2, (line_end.y() + contact_center.y()) / 2)
        painter.drawText(cardinality_start.toPoint(), str(contact['cardinality'][0]))
        painter.drawText(cardinality_end.toPoint(), str(contact['cardinality'][1]))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_H:
            self.showHelpDialog()
        elif event.key() == Qt.Key_S and event.modifiers() & Qt.ControlModifier:
            self.saveAsImage()
        elif event.key() == Qt.Key_S:
            self.saveCoordinates()

    def saveAsImage(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "选择保存路径", "", "PNG Files (*.png);;All Files (*)", options=options)
        if file_path:
            pixmap = self.grab()
            pixmap.save(file_path, "PNG")

    def saveCoordinates(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "选择保存路径", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            # 将索引转换为字符串
            data = {
                "entity": [
                    {
                        "name": entity["name"],
                        "attribute": entity["attribute"],
                        "primaryKey": entity["attribute"][entity["primaryKey"]] if isinstance(entity["primaryKey"], int) else entity["primaryKey"],
                        "foreignKey": [
                            [entity["attribute"][fk[0]], self.ermap.entity[fk[1]]["name"], self.ermap.entity[fk[1]]["attribute"][fk[2]]] if isinstance(fk[0], int) else fk
                            for fk in entity["foreignKey"]
                        ],
                        "x": entity["x"],
                        "y": entity["y"],
                        "attribute_coords": entity["attribute_coords"]
                    }
                    for entity in self.ermap.entity
                ],
                "contact": self.ermap.contact,
            }
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    json.dump(data, file, indent=4, ensure_ascii=False)
                print(f"数据已成功保存到 {file_path}")
            except Exception as e:
                print(f"保存文件时出错: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.selected_entity = self.getEntityAtPosition(event.pos())
            self.selected_contact = self.getContactAtPosition(event.pos())
            self.selected_attribute = self.getAttributeAtPosition(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            if event.modifiers() & Qt.ShiftModifier:
                self.moveEntityAndContact(event)
            elif event.modifiers() & Qt.AltModifier:
                self.moveCanvas(event)
            elif self.selected_attribute:
                self.moveSelectedAttribute(event)
            elif self.selected_entity:
                self.moveSelectedEntity(event)
            elif self.selected_contact:
                self.moveSelectedContact(event)

    def getEntityAtPosition(self, pos):
        for entity in self.ermap.entity:
            rect = QRectF(entity['x'], entity['y'], 100, 50)
            if rect.contains(pos):
                return entity
        return None

    def getContactAtPosition(self, pos):
        for contact in self.ermap.contact:
            center_x = contact['x'] + 50
            center_y = contact['y'] + 25
            diamond = [
                QPointF(center_x, center_y - 25),
                QPointF(center_x + 50, center_y),
                QPointF(center_x, center_y + 25),
                QPointF(center_x - 50, center_y)
            ]
            polygon = QPolygonF(diamond)
            if polygon.containsPoint(pos, Qt.OddEvenFill):
                return contact
        return None

    def getAttributeAtPosition(self, pos):
        for entity in self.ermap.entity:
            for i, coords in enumerate(entity['attribute_coords']):
                attr_x, attr_y = coords
                ellipse = QRectF(attr_x, attr_y, 100, 50)
                if ellipse.contains(pos):
                    return (entity, i)
        for contact in self.ermap.contact:
            for i, coords in enumerate(contact['attribute_coords']):
                attr_x, attr_y = coords
                ellipse = QRectF(attr_x, attr_y, 100, 50)
                if ellipse.contains(pos):
                    return (contact, i)
        return None

    def moveSelectedEntity(self, event):
        dx = event.pos().x() - self.drag_start_position.x()
        dy = event.pos().y() - self.drag_start_position.y()
        self.drag_start_position = event.pos()

        self.selected_entity['x'] += dx
        self.selected_entity['y'] += dy
        self.update()

    def moveSelectedContact(self, event):
        dx = event.pos().x() - self.drag_start_position.x()
        dy = event.pos().y() - self.drag_start_position.y()
        self.drag_start_position = event.pos()
    
        if self.selected_contact:
            self.selected_contact['x'] += dx
            self.selected_contact['y'] += dy
        self.update()

    def moveSelectedAttribute(self, event):
        dx = event.pos().x() - self.drag_start_position.x()
        dy = event.pos().y() - self.drag_start_position.y()
        self.drag_start_position = event.pos()
    
        if self.selected_attribute:
            entity, index = self.selected_attribute
            entity['attribute_coords'][index][0] += dx
            entity['attribute_coords'][index][1] += dy
        self.update()

    def moveCanvas(self, event):
        dx = event.pos().x() - self.drag_start_position.x()
        dy = event.pos().y() - self.drag_start_position.y()
        self.drag_start_position = event.pos()
    
        for entity in self.ermap.entity:
            entity['x'] += dx
            entity['y'] += dy
            for coord in entity['attribute_coords']:
                coord[0] += dx
                coord[1] += dy
    
        for contact in self.ermap.contact:
            contact['x'] += dx
            contact['y'] += dy
            for coord in contact['attribute_coords']:
                coord[0] += dx
                coord[1] += dy
    
        self.update()

    def moveEntityAndContact(self, event):
        dx = event.pos().x() - self.drag_start_position.x()
        dy = event.pos().y() - self.drag_start_position.y()
        self.drag_start_position = event.pos()

        if self.selected_entity:
            self.selected_entity['x'] += dx
            self.selected_entity['y'] += dy
            for i in range(len(self.selected_entity['attribute_coords'])):
                self.selected_entity['attribute_coords'][i][0] += dx
                self.selected_entity['attribute_coords'][i][1] += dy

        if self.selected_contact:
            self.selected_contact['x'] += dx
            self.selected_contact['y'] += dy
            for i in range(len(self.selected_contact['attribute_coords'])):
                self.selected_contact['attribute_coords'][i][0] += dx
                self.selected_contact['attribute_coords'][i][1] += dy

        self.update()

class createContactGui(QWidget):
    def __init__(self, ermap):
        super().__init__()
        self.ermap = ermap
        self.initUI()

    def initUI(self):
        self.setWindowTitle("创建联系")
        self.setGeometry(100, 100, 1200, 800)
    
        main_layout = QHBoxLayout(self)
    
        # 左侧部分
        self.left_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_content.setStyleSheet("background-color: #f0f0f0;")
        self.scroll_area.setWidget(self.scroll_content)
        self.left_layout.addWidget(self.scroll_area)
        main_layout.addLayout(self.left_layout, 3)
    
        # 右侧部分
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop)
    
        self.new_contact_btn = QPushButton("新建关系")
        self.new_contact_btn.clicked.connect(self.showNewContactDialog)
        right_layout.addWidget(self.new_contact_btn)
    
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.saveData)
        right_layout.addWidget(self.save_btn)
    
        right_layout.addStretch(1)
    
        self.adjust_entity_btn = QPushButton("调整实体")
        self.adjust_entity_btn.clicked.connect(self.adjustEntity)
        right_layout.addWidget(self.adjust_entity_btn)
    
        self.start_drawing_btn = QPushButton("开始绘图")
        self.start_drawing_btn.clicked.connect(self.startDrawing)
        right_layout.addWidget(self.start_drawing_btn)
    
        main_layout.addLayout(right_layout, 1)
    
        self.setLayout(main_layout)
        self.updateContactList()
    
        # 调整窗口位置到屏幕中央
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def updateContactList(self):
        # 删除左侧的滚动区域
        self.left_layout.removeWidget(self.scroll_area)
        self.scroll_area.deleteLater()

        # 重新创建左侧的滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_content.setStyleSheet("background-color: #f0f0f0;")
        self.scroll_area.setWidget(self.scroll_content)
        self.left_layout.addWidget(self.scroll_area)

        # 遍历所有联系并创建对应的界面元素
        for contact in self.ermap.contact:
            contact_layout = QVBoxLayout()
            contact_layout.setContentsMargins(10, 10, 10, 10)
            contact_layout.setSpacing(10)

            contact_widget = QWidget()
            contact_widget.setLayout(contact_layout)
            contact_widget.setStyleSheet("background-color: #e0e0e0; border: 1px solid #d0d0d0; border-radius: 5px;")
            contact_widget.setMaximumHeight(200)  # 设置每行的最大高度

            contact_label = QLabel(f"名称: {contact['name']}\n实体: {contact['twoEntities']}\n基数: {contact['cardinality']}\n属性：{contact['attribute']}")
            contact_layout.addWidget(contact_label)

            button_layout = QHBoxLayout()
            modify_btn = QPushButton("修改")
            modify_btn.clicked.connect(lambda _, c=contact: self.showModifyContactDialog(c))
            button_layout.addWidget(modify_btn)

            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda _, c=contact: self.deleteContact(c))
            button_layout.addWidget(delete_btn)

            contact_layout.addLayout(button_layout)

            self.scroll_layout.addWidget(contact_widget)

        # 在布局的底部添加一个弹性空间
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.scroll_layout.addItem(spacer)

    def showNewContactDialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("新建关系")
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)  # 去掉右上角的问号
        dialog.resize(800, 400)  # 设置窗口宽度

        dialog_layout = QFormLayout(dialog)

        name_input = QTextEdit()
        name_input.setPlaceholderText("关系名字")
        name_input.setMinimumWidth(400)  # 设置最小宽度
        name_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("名称:", name_input)

        entity1_input = QComboBox()
        entity1_input.addItems([entity["name"] for entity in self.ermap.entity])
        dialog_layout.addRow("实体1:", entity1_input)

        entity2_input = QComboBox()
        entity2_input.addItems([entity["name"] for entity in self.ermap.entity])
        dialog_layout.addRow("实体2:", entity2_input)

        cardinality_input = QLineEdit()
        cardinality_input.setPlaceholderText("基数 (格式: 1,10)")
        dialog_layout.addRow("基数:", cardinality_input)

        attribute_input = QTextEdit()
        attribute_input.setPlaceholderText("属性列表，用英文逗号隔开")
        attribute_input.setMinimumWidth(400)  # 设置最小宽度
        attribute_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("属性:", attribute_input)

        error_label = QLabel("")
        error_label.setStyleSheet("color: red")
        dialog_layout.addRow(error_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.createContact(dialog, name_input, entity1_input, entity2_input, cardinality_input, attribute_input, error_label))
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addRow(button_box)

        dialog.exec_()

    def createContact(self, dialog, name_input, entity1_input, entity2_input, cardinality_input, attribute_input, error_label):
        name = name_input.toPlainText().strip()
        entity1 = entity1_input.currentText()
        entity2 = entity2_input.currentText()
        cardinality = tuple(cardinality_input.text().strip().split(','))
        attribute = [attr.strip() for attr in attribute_input.toPlainText().split(',')]

        if len(cardinality) != 2:
            error_label.setText("基数格式不正确，应为两个字符串，用逗号分隔")
            return

        if entity1 == entity2:
            error_label.setText("实体不能自己关联自己")
            return

        try:
            self.ermap.createContact(name, (entity1, entity2), cardinality, attribute)
            dialog.accept()
            self.updateContactList()
        except ValueError as e:
            error_label.setText(str(e))

    def showModifyContactDialog(self, contact):
        dialog = QDialog(self)
        dialog.setWindowTitle("修改关系")
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)  # 去掉右上角的问号
        dialog.resize(800, 400)  # 设置窗口宽度
    
        dialog_layout = QFormLayout(dialog)
    
        name_input = QTextEdit(contact["name"])
        name_input.setMinimumWidth(400)  # 设置最小宽度
        name_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("名称:", name_input)
    
        entity1_input = QComboBox()
        entity1_input.addItems([entity["name"] for entity in self.ermap.entity])
        entity1_input.setCurrentText(contact["twoEntities"][0])
        dialog_layout.addRow("实体1:", entity1_input)
    
        entity2_input = QComboBox()
        entity2_input.addItems([entity["name"] for entity in self.ermap.entity])
        entity2_input.setCurrentText(contact["twoEntities"][1])
        dialog_layout.addRow("实体2:", entity2_input)
    
        cardinality_input = QLineEdit(",".join(map(str, contact["cardinality"])))
        dialog_layout.addRow("基数:", cardinality_input)
    
        attribute_input = QTextEdit(",".join(contact["attribute"]))
        attribute_input.setMinimumWidth(400)  # 设置最小宽度
        attribute_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("属性:", attribute_input)
    
        error_label = QLabel("")
        error_label.setStyleSheet("color: red")
        dialog_layout.addRow(error_label)
    
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.modifyContact(dialog, contact, name_input, entity1_input, entity2_input, cardinality_input, attribute_input, error_label))
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addRow(button_box)
    
        dialog.exec_()
    
    def modifyContact(self, dialog, contact, name_input, entity1_input, entity2_input, cardinality_input, attribute_input, error_label):
        name = name_input.toPlainText().strip()
        entity1 = entity1_input.currentText()
        entity2 = entity2_input.currentText()
        cardinality = tuple(cardinality_input.text().strip().split(','))
        attribute = [attr.strip() for attr in attribute_input.toPlainText().split(',')]

        if len(cardinality) != 2:
            error_label.setText("基数格式不正确，应为两个字符串，用逗号分隔")
            return

        try:
            contact["name"] = name
            contact["twoEntities"] = (entity1, entity2)
            contact["cardinality"] = cardinality
            contact["attribute"] = attribute
            dialog.accept()
            self.updateContactList()
        except ValueError as e:
            error_label.setText(str(e))

    def deleteContact(self, contact):
        reply = QMessageBox.question(self, '确认删除', f"确定要删除关系 '{contact['name']}' 吗?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.ermap.contact.remove(contact)
            self.updateContactList()

    def saveData(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "选择保存路径", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            self.ermap.save(file_path)

    def adjustEntity(self):
        self.close()
        self.entity_gui = createEntityGui(self.ermap)
        self.entity_gui.show()

    def startDrawing(self):
        self.close()
        self.main_gui = mainGui(self.ermap)
        self.main_gui.show()

class createEntityGui(QWidget):
    def __init__(self, ermap):
        super().__init__()
        self.ermap = ermap
        self.initUI()

    def initUI(self):
        self.setWindowTitle("创建实体")
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QHBoxLayout(self)
        
        # 左侧部分
        self.left_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_content.setStyleSheet("background-color: #f0f0f0;")
        self.scroll_area.setWidget(self.scroll_content)
        self.left_layout.addWidget(self.scroll_area)
        main_layout.addLayout(self.left_layout, 3)

        # 右侧部分
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignTop)

        self.new_entity_btn = QPushButton("新建实体")
        self.new_entity_btn.clicked.connect(self.showNewEntityDialog)
        right_layout.addWidget(self.new_entity_btn)

        self.import_data_btn = QPushButton("导入数据")
        self.import_data_btn.clicked.connect(self.importData)
        right_layout.addWidget(self.import_data_btn)

        right_layout.addStretch(1)

        self.next_btn = QPushButton("下一步")
        self.next_btn.clicked.connect(self.nextStep)
        right_layout.addWidget(self.next_btn, alignment=Qt.AlignBottom)

        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)
        self.updateEntityList()

        # 调整窗口位置到屏幕中央
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def showModifyEntityDialog(self, entity):
        dialog = QDialog(self)
        dialog.setWindowTitle("修改实体")
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)  # 去掉右上角的问号
        dialog.resize(800, 400)  # 设置窗口宽度

        dialog_layout = QFormLayout(dialog)

        name_input = QTextEdit(entity["name"])
        name_input.setMinimumWidth(400)  # 设置最小宽度
        name_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("名称:", name_input)

        attribute_input = QTextEdit(",".join(entity["attribute"]))
        attribute_input.setMinimumWidth(400)  # 设置最小宽度
        attribute_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("属性:", attribute_input)

        primary_key_input = QTextEdit(entity["primaryKey"])
        primary_key_input.setMinimumWidth(400)  # 设置最小宽度
        primary_key_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("主键:", primary_key_input)

        foreign_key_input = QTextEdit(";".join([",".join(fk) for fk in entity["foreignKey"]]))
        foreign_key_input.setMinimumWidth(400)  # 设置最小宽度
        foreign_key_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("外键:", foreign_key_input)

        error_label = QLabel("")
        error_label.setStyleSheet("color: red")
        dialog_layout.addRow(error_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.modifyEntity(dialog, entity, name_input, attribute_input, primary_key_input, foreign_key_input, error_label))
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addRow(button_box)

        # 调整窗口位置到屏幕中央
        screen = QDesktopWidget().screenGeometry()
        size = dialog.geometry()
        dialog.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

        dialog.exec_()

    
    def updateEntityList(self):
        # 删除左侧的滚动区域
        self.left_layout.removeWidget(self.scroll_area)
        self.scroll_area.deleteLater()

        # 重新创建左侧的滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_content.setStyleSheet("background-color: #f0f0f0;")
        self.scroll_area.setWidget(self.scroll_content)
        self.left_layout.addWidget(self.scroll_area)

        # 遍历所有实体并创建对应的界面元素
        for entity in self.ermap.entity:
            entity_layout = QVBoxLayout()
            entity_layout.setContentsMargins(10, 10, 10, 10)
            entity_layout.setSpacing(10)

            entity_widget = QWidget()
            entity_widget.setLayout(entity_layout)
            entity_widget.setStyleSheet("background-color: #e0e0e0; border: 1px solid #d0d0d0; border-radius: 5px;")
            entity_widget.setMaximumHeight(200)  # 设置每行的最大高度

            entity_label = QLabel(f"名称: {entity['name']}\n属性: {entity['attribute']}\n主键: {entity['primaryKey']}\n外键: {entity['foreignKey']}")
            entity_layout.addWidget(entity_label)

            button_layout = QHBoxLayout()
            modify_btn = QPushButton("修改")
            modify_btn.clicked.connect(lambda _, e=entity: self.showModifyEntityDialog(e))
            button_layout.addWidget(modify_btn)

            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda _, e=entity: self.deleteEntity(e))
            button_layout.addWidget(delete_btn)

            entity_layout.addLayout(button_layout)

            self.scroll_layout.addWidget(entity_widget)

        # 在布局的底部添加一个弹性空间
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.scroll_layout.addItem(spacer)

    def showNewEntityDialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("新建实体")
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)  # 去掉右上角的问号
        dialog.resize(800, 400)  # 设置窗口宽度

        dialog_layout = QFormLayout(dialog)

        name_input = QTextEdit()
        name_input.setPlaceholderText("实体名字")
        name_input.setMinimumWidth(400)  # 设置最小宽度
        name_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("名称:", name_input)

        attribute_input = QTextEdit()
        attribute_input.setPlaceholderText("属性列表，用英文逗号隔开")
        attribute_input.setMinimumWidth(400)  # 设置最小宽度
        attribute_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("属性:", attribute_input)

        primary_key_input = QTextEdit()
        primary_key_input.setPlaceholderText("主键，属性列表里面必须存在主键对应的元素")
        primary_key_input.setMinimumWidth(400)  # 设置最小宽度
        primary_key_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("主键:", primary_key_input)

        foreign_key_input = QTextEdit()
        foreign_key_input.setPlaceholderText("每一个元素有三个参数,分别是 (拥有外键的字段 外键指向的实体 实体对应的属性) 元素之间用分号隔开，括号里面的内容用英文逗号隔开")
        foreign_key_input.setMinimumWidth(400)  # 设置最小宽度
        foreign_key_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("外键:", foreign_key_input)

        error_label = QLabel("")
        error_label.setStyleSheet("color: red")
        dialog_layout.addRow(error_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.createEntity(dialog, name_input, attribute_input, primary_key_input, foreign_key_input, error_label))
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addRow(button_box)

        dialog.exec_()

    def createEntity(self, dialog, name_input, attribute_input, primary_key_input, foreign_key_input, error_label):
        name = name_input.toPlainText().strip()
        attribute = [attr.strip() for attr in attribute_input.toPlainText().split(',')]
        primary_key = primary_key_input.toPlainText().strip() or ""
        foreign_key = [fk.strip().split(',') for fk in foreign_key_input.toPlainText().split(';') if fk.strip()]
    
        try:
            # 检查 primaryKey
            if primary_key and primary_key not in attribute:
                raise ValueError(f"primaryKey '{primary_key}' 不在 attribute 列表中")
    
            # 检查 foreignKey
            for fk in foreign_key:
                if fk[0] not in attribute:
                    raise ValueError(f"foreignKey 的字段 '{fk[0]}' 不在 attribute 列表中")
    
                entity_names = [e["name"] for e in self.ermap.entity]
                if fk[1] not in entity_names:
                    raise ValueError(f"foreignKey 指向的实体 '{fk[1]}' 不存在")
    
                target_entity = next(e for e in self.ermap.entity if e["name"] == fk[1])
                if fk[2] not in target_entity["attribute"]:
                    raise ValueError(f"foreignKey 指向的属性 '{fk[2]}' 不在目标实体的 attribute 列表中")
    
            self.ermap.createEntity(name, attribute, primary_key, foreign_key)
            dialog.accept()
            self.updateEntityList()
        except ValueError as e:
            error_label.setText(str(e))

    def showModifyEntityDialog(self, entity):
        dialog = QDialog(self)
        dialog.setWindowTitle("修改实体")
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)  # 去掉右上角的问号
        dialog.resize(800, 400)  # 设置窗口宽度

        dialog_layout = QFormLayout(dialog)

        name_input = QTextEdit(entity["name"])
        name_input.setMinimumWidth(400)  # 设置最小宽度
        name_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("名称:", name_input)

        attribute_input = QTextEdit(",".join(entity["attribute"]))
        attribute_input.setMinimumWidth(400)  # 设置最小宽度
        attribute_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("属性:", attribute_input)

        primary_key_input = QTextEdit(entity["primaryKey"])
        primary_key_input.setMinimumWidth(400)  # 设置最小宽度
        primary_key_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("主键:", primary_key_input)

        foreign_key_input = QTextEdit(";".join([",".join(fk) for fk in entity["foreignKey"]]))
        foreign_key_input.setMinimumWidth(400)  # 设置最小宽度
        foreign_key_input.setMinimumHeight(60)  # 设置最小高度
        dialog_layout.addRow("外键:", foreign_key_input)

        error_label = QLabel("")
        error_label.setStyleSheet("color: red")
        dialog_layout.addRow(error_label)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.modifyEntity(dialog, entity, name_input, attribute_input, primary_key_input, foreign_key_input, error_label))
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addRow(button_box)

        # 调整窗口位置到屏幕中央
        screen = QDesktopWidget().screenGeometry()
        size = dialog.geometry()
        dialog.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

        dialog.exec_()

    def modifyEntity(self, dialog, entity, name_input, attribute_input, primary_key_input, foreign_key_input, error_label):
        name = name_input.toPlainText().strip()
        attribute = [attr.strip() for attr in attribute_input.toPlainText().split(',')]
        primary_key = primary_key_input.toPlainText().strip() or ""
        foreign_key = [fk.strip().split(',') for fk in foreign_key_input.toPlainText().split(';') if fk.strip()]
    
        try:
            # 检查 primaryKey
            if primary_key and primary_key not in attribute:
                raise ValueError(f"primaryKey '{primary_key}' 不在 attribute 列表中")
    
            # 检查 foreignKey
            for fk in foreign_key:
                if fk[0] not in attribute:
                    raise ValueError(f"foreignKey 的字段 '{fk[0]}' 不在 attribute 列表中")
    
                entity_names = [e["name"] for e in self.ermap.entity]
                if fk[1] not in entity_names:
                    raise ValueError(f"foreignKey 指向的实体 '{fk[1]}' 不存在")
    
                target_entity = next(e for e in self.ermap.entity if e["name"] == fk[1])
                if fk[2] not in target_entity["attribute"]:
                    raise ValueError(f"foreignKey 指向的属性 '{fk[2]}' 不在目标实体的 attribute 列表中")
    
            entity["name"] = name
            entity["attribute"] = attribute
            entity["primaryKey"] = primary_key
            entity["foreignKey"] = foreign_key
            dialog.accept()
            self.updateEntityList()
        except ValueError as e:
            error_label.setText(str(e))

    def deleteEntity(self, entity):
        reply = QMessageBox.question(self, '确认删除', f"确定要删除实体 '{entity['name']}' 吗?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.ermap.entity.remove(entity)
            self.updateEntityList()

    def importData(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "选择数据文件", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            self.ermap.read(file_path)
            self.updateEntityList()

    def nextStep(self):
        self.close()
        self.contact_gui = createContactGui(self.ermap)
        self.contact_gui.show()

class erMap:
    entity:list = []
    contact:list = []
    window = None
    
    def __init__(self):
        print("版本：1.0")
        print("调用start方法以启动。")

    def start(self):
        """初始化时直接创建并显示窗口"""
        self.app = QApplication(sys.argv)
        self.window = createEntityGui(self)  # 使用 createEntityGui 作为主窗口
        self.window.setWindowTitle("er图绘制")
        self.window.show()
        sys.exit(self.app.exec_())

    def initialization(self) -> None:
        for ent in self.entity:
            # 检查 attribute 列表是否仅包含一个空字符串
            if ent["attribute"] == [""]:
                ent["primaryKey"] = ""
            else:
                # 处理 primaryKey
                if ent["primaryKey"] in ent["attribute"]:
                    ent["primaryKey"] = ent["attribute"].index(ent["primaryKey"])
                elif ent["primaryKey"] == "":
                    pass
                else:
                    raise ValueError(f"primaryKey '{ent['primaryKey']}' 不在 attribute 列表中")
        
            # 处理 foreignKey
            for fk in ent["foreignKey"]:
                if fk[0] in ent["attribute"]:
                    fk[0] = ent["attribute"].index(fk[0])
                else:
                    raise ValueError(f"foreignKey 的字段 '{fk[0]}' 不在 attribute 列表中")
        
                # 查找外键指向的实体
                entity_names = [e["name"] for e in self.entity]
                if fk[1] in entity_names:
                    fk[1] = entity_names.index(fk[1])
                else:
                    raise ValueError(f"foreignKey 指向的实体 '{fk[1]}' 不存在")
        
                # 查找外键指向的属性
                target_entity = self.entity[fk[1]]
                if fk[2] in target_entity["attribute"]:
                    fk[2] = target_entity["attribute"].index(fk[2])
                else:
                    raise ValueError(f"foreignKey 指向的属性 '{fk[2]}' 不在目标实体的 attribute 列表中")
                
    def createEntity(self, name: str,attribute: list[str], primaryKey: str, foreignKey: list[list[str]]) -> None:
        """
        创建一个实体对象。
        参数:
            name (str): 实体的名称。
            attribute (List[str]): 实体的其他属性列表。
            primaryKey (str): 实体的主键。
            foreignKey ([[str, str, str], ...]): 实体的外键列表，0：拥有外键的字段，1，2：外键指向的实体和属性。
        """
        if not name:
            raise ValueError("实体名称不能为空")
        
        self.entity.append({
            "name": name,
            "primaryKey": primaryKey,
            "foreignKey": foreignKey,
            "attribute": attribute,
        })
    
    def createContact(self, name:str, twoEntities:tuple[str,str], cardinality:tuple[str,str], attribute: list[str]) -> None:
        """
        创建一个联系对象。
        参数:
            name (str): 联系的名称。
            twoEntities (Tuple[str, str]): 关联的两个实体名称，格式为 (实体1, 实体2)。
            cardinality (Tuple[str, str]): 联系的基数，格式为 (基数1, 基数2)。
            attribute (List[str]): 联系的属性列表。
        注：twoEntities cardinality一一对应
        """
        if not name:
            raise ValueError("联系名称不能为空")
        if len(twoEntities) != 2:
            raise ValueError("two_entities 必须包含两个实体")
        if len(cardinality) != 2:
            raise ValueError("cardinality 必须包含两个字符串")
        
        self.contact.append({
            "name": name,
            "twoEntities": twoEntities,
            "cardinality": cardinality,
            "attribute": attribute,
        })

    def save(self, file_path: str) -> None:
        """
        将当前对象的属性保存为 JSON 文件。
        参数:
            file_path (str): 保存文件的路径。
        """
        data = {
            "entity": self.entity,
            "contact": self.contact,
        }

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            print(f"数据已成功保存到 {file_path}")
        except Exception as e:
            print(f"保存文件时出错: {e}")

    def read(self, file_path: str) -> None:
        """
        从 JSON 文件中读取数据并加载到当前对象的属性中。
        参数:
            file_path (str): 读取文件的路径。
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.entity = data.get("entity", [])
                self.contact = data.get("contact", [])
            print(f"数据已成功从 {file_path} 读取")
        except Exception as e:
            print(f"读取文件时出错: {e}")


if __name__ == "__main__":

    # 读取文件
    ermap = erMap()
    ermap.start()
    # ermap.read("ermap_data.json")
    # # 创建 Student 实体
    # ermap.createEntity(
    #     name="Student",
    #     attribute=["student_id", "name", "age", "teacher_id"],
    #     primaryKey="student_id",
    #     foreignKey=[["teacher_id", "Teacher", "teacher_id"]],  # teacher_id 是外键，指向 Teacher 的 teacher_id
    # )

    # # 创建 Teacher 实体
    # ermap.createEntity(
    #     name="Teacher",
    #     attribute=["teacher_id", "name", "subject"],
    #     primaryKey="teacher_id",
    #     foreignKey=[],  # Teacher 没有外键
    # )

    # # 创建 Teach 联系
    # ermap.createContact(
    #     name="Teach",
    #     twoEntities=("Teacher", "Student"),  # 关联 Teacher 和 Student
    #     cardinality=("1", "10"),  # 一个老师可以教最多 10 个学生
    #     attribute=["nud,lad"]
    # )

    # # 保存到文件
    # ermap.save("ermap_data.json")
