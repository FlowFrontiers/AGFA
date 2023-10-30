from pandas import DataFrame
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from os import path, mkdir
from numpy import zeros, linspace
from csv import DictWriter


dirname = path.dirname(__file__)


class ExporterController:
    ticker=0
    buffer_animaton = []
    TCHanimation, ARUanimation, x_axes = [], [], []
    buffer0, buffer1, buffer2, buffer3, buffer4, buffer5 = [], [], [], [], [], []

    export_num = 1
    buffer_export_step = 1

    def buildUpAnimationArray(self,length):
        temp_zeros = zeros((int(length)), dtype=int)
        self.TCHanimation = temp_zeros.copy().tolist()
        self.ARUanimation = temp_zeros.copy().tolist()
        self.Tanimation = temp_zeros.copy().tolist()
        self.buffer0 = temp_zeros.copy().tolist()
        self.buffer1 = temp_zeros.copy().tolist()
        self.buffer2 = temp_zeros.copy().tolist()
        self.buffer3 = temp_zeros.copy().tolist()
        self.buffer4 = temp_zeros.copy().tolist()
        self.buffer5 = temp_zeros.copy().tolist()
        self.x_axes = linspace(1,int(length),int(length)+1).tolist()

    def loadData(self,bufferArray):
        values = []

        for buffer in bufferArray:
            values.append(len(buffer.bufferedArray))

        data = {'Buffer': ['B0', 'B1', 'B2', 'B3', 'B4', 'B5'],
                'Element': [values[0], values[1], values[2], values[3], values[4], values[5]]
                }
        df = DataFrame(data, columns=['Buffer', 'Element'])
        return df

    def moveBuffer(self,bufferArray):
        self.buffer0.pop(0)
        self.buffer1.pop(0)
        self.buffer2.pop(0)
        self.buffer3.pop(0)
        self.buffer4.pop(0)
        self.buffer5.pop(0)

        values = []
        for buffer in bufferArray:
            values.append(len(buffer.bufferedArray))

        self.buffer0.append(values[0])
        self.buffer1.append(values[1])
        self.buffer2.append(values[2])
        self.buffer3.append(values[3])
        self.buffer4.append(values[4])
        self.buffer5.append(values[5])

    def moveT(self,T):
        self.Tanimation.pop(0)
        self.Tanimation.append(T)

    def moveTCHandARU(self,TCH_temp,ARU_temp):
        self.TCHanimation.pop(0)
        self.TCHanimation.append(TCH_temp)

        self.ARUanimation.pop(0)
        self.ARUanimation.append(ARU_temp)

    def __init__(self,bufferArray, ARU_t0, TCh_t0, tick, graphLength, graphWidth, grapHeight, fieldNames, T):
        self.tick = tick
        self.fieldNames = fieldNames

        self.buildUpAnimationArray(length=graphLength)

        self.moveTCHandARU(TCH_temp=TCh_t0, ARU_temp=ARU_t0)
        self.moveT(T=T)

        df = self.loadData(bufferArray=bufferArray)

        fig = make_subplots(
            rows=6, cols=1,
            shared_xaxes=False,
            vertical_spacing=0.1,
            subplot_titles=('Elements in each buffer','TCh','ARU','Buffers change','T','Entry ID\'s in buffers'),
            shared_yaxes=False,
            specs=[[{"type": "bar"}],
                   [{"type": "scatter"}],
                   [{"type": "scatter"}],
                   [{"type": "scatter"}],
                   [{"type": "scatter"}],
                   [{"type": "table"}]]
        )

        fig.add_trace(
            go.Bar(x=df['Buffer'],
                   y=df['Element'],
                   legendgroup="group",
                   name='Element number'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.x_axes,
                       y=self.TCHanimation,
                       legendgroup="group2",
                       name='TCh'),
            row=2, col=1
        )

        # ARU
        fig.add_trace(
            go.Scatter(x=self.x_axes,
                       y=self.ARUanimation,
                       legendgroup="group3",
                       name='ARU'),
            row=3, col=1
        )

        fig.add_trace(
            go.Scatter(x=self.x_axes,
                       y=self.buffer0,
                       legendgroup="group4",
                       name='Buffer 0'),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.x_axes,
                       y=self.buffer1,
                       legendgroup="group4",
                       name='Buffer 1'),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.x_axes,
                       y=self.buffer2,
                       legendgroup="group4",
                       name='Buffer 2'),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.x_axes,
                       y=self.buffer3,
                       legendgroup="group4",
                       name='Buffer 3'),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.x_axes,
                       y=self.buffer4,
                       legendgroup="group4",
                       name='Buffer 4'),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(x=self.x_axes,
                       y=self.buffer5,
                       legendgroup="group4",
                       name='Buffer 5'),
            row=4, col=1
        )

        fig.add_trace(
            go.Scatter(x=self.x_axes,
                       y=self.buffer5,
                       legendgroup="group5",
                       name='T value'),
            row=5, col=1
        )

        fig.add_trace(
            go.Table(header=dict(values=df['Buffer'],
                                 font=dict(size=10),
                                 align="left"
                                 ),
                     cells=dict(values=[0,0,0,0,0,0],
                                align="left")
                                ),
            row=6, col=1
        )

        fig.update_layout(
            font=dict(
                family="Computer modern"
            )
        )

        fig['layout']['width'] = int(graphWidth)
        fig['layout']['height'] = int(grapHeight)
        self.fig = fig

    def update_table(self,bufferArray):
        flowArray = []
        for b in bufferArray:
            flow = b.getFlowData()
            temp_flow=[]
            for f in flow:
                temp_flow.append(str(f.id))
            flowArray.append(temp_flow)

        table = self.fig.data[10]
        table.cells=dict(values=[flowArray[0],
                                 flowArray[1],
                                 flowArray[2],
                                 flowArray[3],
                                 flowArray[4],
                                 flowArray[5]])

    def update_buffer_figure(self,bufferArray):
        self.moveBuffer(bufferArray=bufferArray)
        self.fig.data[3].y = self.buffer0
        self.fig.data[4].y = self.buffer1
        self.fig.data[5].y = self.buffer2
        self.fig.data[6].y = self.buffer3
        self.fig.data[7].y = self.buffer4
        self.fig.data[8].y = self.buffer5

    def update_figure(self,bufferArray):
        df = self.loadData(bufferArray=bufferArray)
        bar = self.fig.data[0]
        bar.y = df['Element']

    def update_ARU_TCH(self,ARU_t0, TCh_t0):
        self.moveTCHandARU(ARU_temp=ARU_t0,TCH_temp=TCh_t0)
        aru_scat = self.fig.data[1]
        tch_scat = self.fig.data[2]
        aru_scat.y = self.ARUanimation
        tch_scat.y = self.TCHanimation

    def update_T(self,T):
        self.moveT(T=T)
        self.fig.data[9].y = self.Tanimation

    def export_figure(self):
        global dirname

        if not path.isdir(path.join(dirname, 'exported_data')):
            mkdir(path.join(dirname, 'exported_data'))

        self.fig.write_html(path.join(dirname, f'exported_data/export-{str(self.export_num)} {datetime.now().strftime("%Y-%m-%d_%H:%M")}.html'))

        self.export_num+=1

    def exportCSV(self, bufferArray):
        global dirname

        __exportTime = str(self.buffer_export_step) + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M")

        if not path.isdir(path.join(dirname,'exported_buffers')):
            mkdir(path.join(dirname,'exported_buffers'))

        if not path.isdir(path.join(dirname,f'exported_buffers/step-{__exportTime}')):
            mkdir(path.join(dirname,f'exported_buffers/step-{__exportTime}'))

        if not path.exists(path.join(dirname,f'exported_buffers/step-{__exportTime}/all-buffer-data.csv')):
            with open(path.join(dirname,f'exported_buffers/step-{__exportTime}/all-buffer-data.csv'), 'w') as csv_file:
                __fieldNames = self.fieldNames
                writer = DictWriter(csv_file, fieldnames=__fieldNames)
                writer.writeheader()

        for buffer in bufferArray:
            with open(path.join(dirname,f'exported_buffers/step-{__exportTime}/buffer-{bufferArray.index(buffer)}.csv'), 'w') as csv_file:
                writer = DictWriter(csv_file, fieldnames=self.fieldNames)
                flows = buffer.getFlowData()

                writer.writeheader()

                for flow in flows:
                    writer.writerow(dict(zip(flow.keys(),flow.values())))

            with open(path.join(dirname,f'exported_buffers/step-{__exportTime}/all-buffer-data.csv'), 'a') as csv_file:
                __fieldNames = self.fieldNames
                writer = DictWriter(csv_file, fieldnames=__fieldNames)
                flows = buffer.getFlowData()
                for flow in flows:
                    __values = dict(zip(flow.keys(), flow.values()))
                    writer.writerow(__values)

        self.buffer_export_step += 1

    def update(self,bufferArray, ARU_t0, TCh_t0, T):
        self.update_figure(bufferArray=bufferArray)
        self.update_table(bufferArray=bufferArray)
        self.update_ARU_TCH(ARU_t0=ARU_t0, TCh_t0=TCh_t0)
        self.update_T(T=T)
        self.update_buffer_figure(bufferArray=bufferArray)

        if int(self.tick) == int(self.ticker):
            self.export_figure()
            self.exportCSV(bufferArray=bufferArray)
            self.ticker = 0
        else:
            self.ticker += 1

        if not path.isdir(path.join(dirname, 'exported_data')):
            mkdir(path.join(dirname, 'exported_data'))

        # this part saves out the ARU, TCH and T values
        if path.exists(path.join(dirname,f'exported_data/compute-state.csv')):
            with open(path.join(dirname,f'exported_data/compute-state.csv'), 'a') as csv_file:
                __fieldNames = ['ARU_t0', 'TCh_t0', 'T', 'B0', 'B1', 'B2', 'B3', 'B4', 'B5']
                writer = DictWriter(csv_file, fieldnames=__fieldNames)

                writer.writerow({
                    'ARU_t0': ARU_t0,
                    'TCh_t0': TCh_t0,
                    'T': T,
                    'B0': len(bufferArray[0].bufferedArray),
                    'B1': len(bufferArray[1].bufferedArray),
                    'B2': len(bufferArray[2].bufferedArray),
                    'B3': len(bufferArray[3].bufferedArray),
                    'B4': len(bufferArray[4].bufferedArray),
                    'B5': len(bufferArray[5].bufferedArray)
                })
